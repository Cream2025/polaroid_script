import asyncio
from datetime import datetime
from enum import Enum
from math import ceil


class JobType(Enum):
    GET_PRINTER_STATUS = "GET_PRINTER_STATUS"
    GET_PRINTER_INFO = "GET_PRINTER_INFO"
    PRINT_IMAGE = "PRINT_IMAGE"

class Job:
    def __init__(self, job_type, packets, fallback_packet, future):
        self.job_type = job_type
        self.packets = packets
        self.fallback_packet = fallback_packet
        self.future = future
        self.cancel_event = asyncio.Event()

class InstaxJobRunner:
    def __init__(self, instax):
        self.job_queue = None
        self.loop = None
        self.packet_processed_event = None
        self.job_cancel_event = None
        self.instax = instax
        self.current_job = None

    async def start(self):
        self.job_queue = asyncio.Queue()
        self.loop = asyncio.get_running_loop()
        self.packet_processed_event = asyncio.Event()
        self.job_cancel_event = asyncio.Event()
        asyncio.create_task(self.job_runner())

    async def push_job(self, job_type, packets, fallback_packet=None, future=None):
        await self.job_queue.put(Job(job_type, packets, fallback_packet, future))

    async def job_runner(self):
        while True:
            job = await self.job_queue.get()
            self.log(f'job "{job.job_type.value}" will be processed. packets: {len(job.packets)}')
            await self.process_job(job)
            self.job_queue.task_done()

    async def process_job(self, job):
        self.log(f'process job "{job.job_type.value}" start')
        fallback_packet_sended = False
        success = True
        self.current_job = job
        while job and 0 < len(job.packets):
            if len(job.packets) % 10 == 0:
                self.log(f'job "{job.job_type.value}" packets left to send: {len(job.packets)}')

            packet = job.packets.pop(0)
            try:
                if job.cancel_event.is_set() and not fallback_packet_sended:
                    raise asyncio.CancelledError('cancelled job')

                self.send_packet(packet)
                await asyncio.wait_for(self.packet_processed_event.wait(), timeout=5) # 5초 내에 응답 안오면 실패 처리
            except asyncio.TimeoutError:
                self.log(f'job "{job.job_type.value}" is timeout')
                success = False
            except asyncio.CancelledError:
                self.log(f'job "{job.job_type.value}" is cancelled')
                success = False
            except Exception as e:
                self.log(f'job "{job.job_type.value}" raised exception: {e}')
                success = False
            finally:
                self.packet_processed_event.clear()
                # print image 같은 경우는 실패했을 시, download cancel packet을 보내줘야함
                if not success and job.fallback_packet and not fallback_packet_sended:
                    self.log(f'job "{job.job_type.value}" has fallback packet. try to send fallback packet')
                    job.packets = [job.fallback_packet]
                    fallback_packet_sended = True

        if job.future and not job.future.done():
            self.log(f'job "{job.job_type.value}" result: {success}')
            job.future.get_loop().call_soon_threadsafe(job.future.set_result, success)

        self.current_job = None
        self.log(f'process job "{job.job_type.value}" end')

    def send_packet(self, packet):
        """ Send a packet to the printer """
        if not self.instax.dummyPrinter and not self.instax.quiet:
            if not self.instax.peripheral:
                self.log("no peripheral to send packet to")
            elif not self.instax.peripheral.is_connected():
                self.log("peripheral not connected")

        try:
            smallPacketSize = 241
            numberOfParts = ceil(len(packet) / smallPacketSize)
            # self.log(f"> number of parts to send: {numberOfParts}")
            for subPartIndex in range(numberOfParts):
                # self.log((subPartIndex + 1), '/', numberOfParts)
                subPacket = packet[subPartIndex * smallPacketSize:subPartIndex * smallPacketSize + smallPacketSize]

                if not self.instax.dummyPrinter:
                    self.instax.peripheral.write_command(self.instax.serviceUUID, self.instax.writeCharUUID, subPacket)

        except Exception as e:
            raise e

    def on_packet_processed(self):
        self.loop.call_soon_threadsafe(self.packet_processed_event.set)

    def on_job_cancelled(self):
        self.current_job.cancel_event.set()

    def is_queue_empty(self):
        return self.job_queue.empty()

    def is_print_image_processing(self):
        return self.current_job and self.current_job.job_type == JobType.PRINT_IMAGE and 0 < len(self.current_job.packets)

    def log(self, message):
        print(f"[{datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}] {message}")