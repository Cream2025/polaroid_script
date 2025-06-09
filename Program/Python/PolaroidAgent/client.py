import asyncio
import atexit

from settings import POLAROID_ID
from utils.instax_ble.InstaxBLE import InstaxBLE
from utils.instax_ble.InstaxJobRunner import InstaxJobRunner
from utils.socket.polaroid_socket_client import PolaroidSocketClient
from typing import Optional

socket_client: Optional[PolaroidSocketClient] = None
instax: Optional[InstaxBLE] = None

def clear_resource():
    global socket_client
    global instax
    if socket_client:
        print('Clear Resource... Close socket')
        socket_client.close()
    if instax:
        print('Clear Resource... Disconnect Instax')
        instax.disconnect()

async def main():
    global socket_client
    global instax
    instax = InstaxBLE(device_name=POLAROID_ID, verbose=True)
    instax_job_runner = InstaxJobRunner(instax)
    await instax_job_runner.start()
    instax.jobRunner = instax_job_runner
    socket_client = PolaroidSocketClient(instax)
    socket_client.connect()

    await asyncio.create_task(send_printer_info(socket_client))

    while True:
        msg = input("Enter message (or 'exit' to quit): ")
        if msg.lower() == 'exit':
            break

    clear_resource()

async def send_printer_info(socket_client):
    while True:
        await socket_client.send_printer_info()
        await asyncio.sleep(10)

if __name__ == "__main__":
    atexit.register(clear_resource)
    asyncio.run(main())