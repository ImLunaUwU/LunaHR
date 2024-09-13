# Use this script for debugging your avatar.
import subprocess
import random
import time
from pythonosc import udp_client

if __name__ == "__main__":
    
    vrchat_ip = "127.0.0.1"
    vrchat_port = 9000

    osc_client = udp_client.SimpleUDPClient(vrchat_ip, vrchat_port)

    def simulate_realistic_heart_rate():
        heart_rate = random.randint(60, 180)

        ones_hr = heart_rate % 10
        tens_hr = (heart_rate // 10) % 10
        hundreds_hr = (heart_rate // 100) % 10

        osc_client.send_message("/avatar/parameters/hr/ones_hr", ones_hr)
        osc_client.send_message("/avatar/parameters/hr/tens_hr", tens_hr)
        osc_client.send_message("/avatar/parameters/hr/hundreds_hr", hundreds_hr)
        osc_client.send_message("/avatar/parameters/hr/heart_rate", heart_rate)

        print(f"Sent Random Heart Rate: {hundreds_hr}{tens_hr}{ones_hr} | BPM: {heart_rate}")

    try:
        while True:
            simulate_realistic_heart_rate()
            time.sleep(1)
    except KeyboardInterrupt:
        print("Script terminated by user.")
