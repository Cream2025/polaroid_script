from enum import Enum

# C#쪽 PacketType과 맞춰야함
class PACKET_TYPE(Enum):
    C2K_WHO_AM_I= 12001
    C2K_PRINTER_INFO= 12002

    K2C_REQ_WHO_AM_I = 21001
    K2C_REQ_PRINTER_INFO= 21002
    K2C_REQ_PRINT_PHOTO = 21003