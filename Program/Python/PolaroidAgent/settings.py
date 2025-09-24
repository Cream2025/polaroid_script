import os
from dotenv import load_dotenv

load_dotenv()
SOCKET_HOST=os.getenv("SOCKET_HOST", "127.0.0.1")
SOCKET_PORT=os.getenv("SOCKET_PORT", 5000)
POLAROID_ID=os.getenv("POLAROID_ID", "INSTAX-40297851")