import json

from datetime import datetime
from settings import SOCKET_HOST, SOCKET_PORT, POLAROID_ID
from utils.instax_ble.InstaxBLE import InstaxBLE
from utils.socket.polaroid_packet_type import PACKET_TYPE
from utils.socket.base_socket_client import BaseSocketClient


class PolaroidSocketClient(BaseSocketClient):
    def __init__(self):
        super().__init__(host=SOCKET_HOST, port=SOCKET_PORT)
        self.instax = InstaxBLE(device_name=POLAROID_ID, verbose=True)

        self.message_func_map = {
            PACKET_TYPE.K2C_REQ_PRINTER_INFO: self.send_printer_info,
            PACKET_TYPE.K2C_REQ_WHO_AM_I: self.send_who_am_i,
            PACKET_TYPE.K2C_REQ_PRINT_PHOTO: self.print_photo,
        }

    def message_map(self):
        return {
            PACKET_TYPE.C2K_WHO_AM_I: self.send_who_am_i
        }

    def send_message(self, message_type, **kwargs):
        message = {
            'PacketType': message_type.value,
            'InstaxId': POLAROID_ID,
            **kwargs
        }

        self.send(json.dumps(message))

    def send_who_am_i(self, **kwargs):
        self.send_message(PACKET_TYPE.C2K_WHO_AM_I)

    def send_printer_info(self, **kwargs):
        if not self.instax.peripheral or not self.instax.peripheral.is_connected():
            self.instax.connect(10)

        if self.instax.peripheral and self.instax.peripheral.is_connected():
            self.instax.get_printer_info()
            self.send_message(PACKET_TYPE.C2K_PRINTER_INFO, PhotoCount=self.instax.photosLeft)

    def print_photo(self, ImageUrl, **kwargs):
        # TODO 다운로드 image
        self.log(ImageUrl)
        image_path = "D:\\workspace\\project\\snapism_belly\\Program\\Hybrid.Kiosk.Web\\bin\\Debug\\net8.0\\Print_Smart\\0_f0_Merged.png"

        if not self.instax.peripheral or not self.instax.peripheral.is_connected():
            self.instax.connect(10)

        if self.instax.peripheral and self.instax.peripheral.is_connected():
            self.instax.enable_printing()
            self.instax.print_image(image_path)
            self.instax.wait_one_minute() # TODO 이거 어떻게 할지 생각해보자. 상태 관리를 해놓는것도 괜찮을듯
        else:
            # TODO 실패 처리
            self.log("connection failed")


    def log(self, message):
        print(f"[{datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}] {message}")

    def connect(self):
        super().connect()
        self.send_who_am_i()

    def handle_message(self, message):
        try:
            data = json.loads(message)
            if 'PacketType' not in data:
                raise Exception("There is no type")

            type = PACKET_TYPE(data['PacketType'])
            if type not in self.message_func_map:
                raise Exception(f"PacketType '{type}' does not exist in message func map")

            self.message_func_map[type](**data)
        except Exception as e:
            self.log(str(e))
