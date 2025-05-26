import atexit
import threading

from utils.socket.polaroid_socket_client import PolaroidSocketClient
from typing import Optional

socket_client: Optional[PolaroidSocketClient] = None

def clear_resource():
    global socket_client
    if socket_client:
        print('Clear Resource... Close socket')
        socket_client.close()
        if socket_client.instax:
            print('Clear Resource... Disconnect Instax')
            socket_client.instax.disconnect()

def main():
    global socket_client
    socket_client = PolaroidSocketClient()
    socket_client.connect()

    send_printer_info(socket_client)

    while True:
        msg = input("Enter message (or 'exit' to quit): ")
        if msg.lower() == 'exit':
            break

    clear_resource()

def send_printer_info(socket_client):
    socket_client.send_printer_info()
    threading.Timer(10, send_printer_info, kwargs={"socket_client": socket_client}).start()

if __name__ == "__main__":
    atexit.register(clear_resource)
    main()