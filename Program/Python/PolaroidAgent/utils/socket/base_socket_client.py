import socket
import struct
import threading
import time
from abc import abstractmethod


class BaseSocketClient:
    def __init__(self, host="", port=0):
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
        self.create_socket()

    def create_socket(self):
        if self.socket:
            try:
                self.socket.shutdown(socket.SHUT_RDWR)
                self.close()
            except:
                pass
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        while not self.connected:
            try:
                self.socket.connect((self.host, self.port))
                self.connected = True
                print(f"connected to {self.host}:{self.port}")
                threading.Thread(target=self.handle_server, daemon=True).start()
            except Exception:
                print("Connection Failed. Retrying to connect...")
                time.sleep(5)
                self.create_socket()

    def send(self, message):
        if self.connected:
            try:
                data = self.get_length_prefixed_message(message)
                self.socket.sendall(data)
            except (BrokenPipeError, ConnectionResetError, OSError):
                print("Connection lost. Reconnecting...")
                self.connected = False
                self.create_socket()
                self.connect()
                data = self.get_length_prefixed_message(message)
                self.socket.sendall(data)
            except Exception as e:
                print(f"여기다 : {str(e)}")

    def get_length_prefixed_message(self, message):
        data = message.encode('utf-8')
        length_prefix = struct.pack('I', len(data))
        return length_prefix + data

    def handle_server(self):
        while True:
            try:
                length_prefix = self.socket.recv(4)
                if not length_prefix:
                    continue

                json_length = struct.unpack('I', length_prefix)[0]
                data = self.socket.recv(json_length).decode('utf-8')
                if not data:
                    continue
                self.handle_message(data)
            except ConnectionResetError:
                break
            except Exception as e:
                break

    @abstractmethod
    def handle_message(self, message):
        pass

    def close(self):
        self.socket.close()
        print("connection closed")