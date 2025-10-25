import asyncio
from aiobleserver import BleServer, BleCharacteristic, BleService

async def start_ble():
    server = BleServer()
    service = BleService(uuid="chipbot-service")
    rx_char = BleCharacteristic(uuid="rx", properties=['write'])
    tx_char = BleCharacteristic(uuid="tx", properties=['read', 'notify'])
    service.add_characteristic(rx_char)
    service.add_characteristic(tx_char)
    server.add_service(service)
    await server.start()
    print("BLE advertising as ChipBot")
