import asyncio
from bleak import BleakScanner, BleakClient
from pythonosc import udp_client

HEART_RATE_UUID = "00002a37-0000-1000-8000-00805f9b34fb"

POLAR_H10_NAME = "Polar H10 B71CC122"

vrchat_ip = "127.0.0.1"
vrchat_port = 9000

async def run():
    retry_interval = 10  # seconds
    while True:
        try:
            devices = await BleakScanner.discover()

            polar_h10_device = None
            for device in devices:
                if device.name and POLAR_H10_NAME in device.name:
                    polar_h10_device = device
                    break

            if polar_h10_device:
                print(f"Found Polar H10: {polar_h10_device}")
                async with BleakClient(polar_h10_device.address) as client:
                    await client.start_notify(HEART_RATE_UUID, handle_heart_rate)

                    try:
                        while True:
                            await asyncio.sleep(1)

                    except KeyboardInterrupt:
                        print("Exiting gracefully.")
                        await client.stop_notify(HEART_RATE_UUID)
                        break

            else:
                print("Polar H10 not found. Retrying in {} seconds.".format(retry_interval))
                await asyncio.sleep(retry_interval)

        except Exception as e:
            print(f"Error: {e}")
            print("Retrying in {} seconds.".format(retry_interval))
            await asyncio.sleep(retry_interval)

def handle_heart_rate(sender: int, data: bytearray):
    heart_rate = data[1]
    print(f"Heart Rate: {heart_rate}")

    ones_hr = heart_rate % 10
    tens_hr = (heart_rate // 10) % 10
    hundreds_hr = (heart_rate // 100) % 10

    osc_client = udp_client.SimpleUDPClient(vrchat_ip, vrchat_port)

    osc_client.send_message("/vrchat/heart_rate", [ones_hr, tens_hr, hundreds_hr, heart_rate])

try:
    asyncio.run(run())
except KeyboardInterrupt:
    pass  # Ignore the KeyboardInterrupt error on exit
