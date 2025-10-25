import socket
from zeroconf import Zeroconf, ServiceInfo

async def start_wifi():
    zeroconf = Zeroconf()
    info = ServiceInfo("_http._tcp.local.", "ChipBot._http._tcp.local.", addresses=[socket.inet_aton(socket.gethostbyname(socket.gethostname()))], port=8000)
    zeroconf.register_service(info)
