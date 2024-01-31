import random
import time
from pythonosc import udp_client

vrchat_ip = "127.0.0.1"
vrchat_port = 9000

osc_client = udp_client.SimpleUDPClient(vrchat_ip, vrchat_port)

def simulate_realistic_heart_rate():
    heart_rate = random.randint(60, 100)

    ones_hr = heart_rate % 10
    tens_hr = (heart_rate // 10) % 10
    hundreds_hr = heart_rate // 100

    osc_address = "/vrchat/heart_rate"
    osc_client.send_message(osc_address, [ones_hr, tens_hr, hundreds_hr, heart_rate])

    print(f"Sent Realistic Heart Rate: {hundreds_hr}{tens_hr}{ones_hr} | BPM: {heart_rate}")

if __name__ == "__main__":
    try:
        while True:
            simulate_realistic_heart_rate()
            time.sleep(1) 
    except KeyboardInterrupt:
        print("Script terminated by user.")
