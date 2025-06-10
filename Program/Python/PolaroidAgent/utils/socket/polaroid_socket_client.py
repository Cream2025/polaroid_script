import asyncio
import json
import os

from datetime import datetime
from urllib.parse import urlparse

import requests

from settings import SOCKET_HOST, SOCKET_PORT, POLAROID_ID
from utils.instax_ble.InstaxBLE import InstaxBLE
from utils.socket.polaroid_packet_type import PACKET_TYPE
from utils.socket.base_socket_client import BaseSocketClient


class PolaroidSocketClient(BaseSocketClient):
    def __init__(self, instax):
        super().__init__(host=SOCKET_HOST, port=SOCKET_PORT)
        self.instax = instax

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

    async def send_printer_info(self, **kwargs):
        if not self.instax.peripheral or not self.instax.peripheral.is_connected():
            await self.instax.connect(10)

        if self.instax.peripheral and self.instax.peripheral.is_connected():
            await self.instax.get_printer_info()
            self.send_message(PACKET_TYPE.C2K_PRINTER_INFO, PhotoCount=self.instax.photosLeft)

    async def print_photo(self, ImageUrl, RequestId, **kwargs):
        image_path = self.download_image(ImageUrl)

        if not self.instax.peripheral or not self.instax.peripheral.is_connected():
            await self.instax.connect(20)

        if self.instax.peripheral and self.instax.peripheral.is_connected():
            self.instax.enable_printing()
            result = await self.instax.print_image(image_path)
            self.send_message(PACKET_TYPE.C2K_RES_PRINT_PHOTO, PrintComplete=result, RequestId=RequestId)
        else:
            self.send_message(PACKET_TYPE.C2K_RES_PRINT_PHOTO, PrintComplete=False, RequestId=RequestId)


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

            asyncio.run(self.message_func_map[type](**data))
        except Exception as e:
            self.log(str(e))

    def download_image(self, image_file_url):
        response = requests.get(image_file_url)
        response.raise_for_status()  # 에러 발생 시 예외

        # 확장자 추출
        parsed_url = urlparse(image_file_url)
        path = parsed_url.path
        ext = os.path.splitext(path)[-1]  # .jpg, .png 등

        # 저장할 파일 이름
        filename = f"print{ext}"
        filepath = os.path.join(os.getcwd(), filename)

        # 저장
        with open(filepath, 'wb') as f:
            f.write(response.content)

        self.log(f"Image({image_file_url} ) saved as {filepath}")

        return filepath