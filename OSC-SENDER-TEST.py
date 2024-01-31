import subprocess

def install_dependencies():
    required_packages = ["python-osc"]

    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            print(f"Installing {package}...")
            subprocess.check_call(["pip", "install", package])

if __name__ == "__main__":
    install_dependencies()
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

        osc_client.send_message("/avatar/parameters/ones_hr", ones_hr)
        osc_client.send_message("/avatar/parameters/tens_hr", tens_hr)
        osc_client.send_message("/avatar/parameters/hundreds_hr", hundreds_hr)
        osc_client.send_message("/avatar/parameters/heart_rate", heart_rate)

        print(f"Sent Realistic Heart Rate: {hundreds_hr}{tens_hr}{ones_hr} | BPM: {heart_rate}")

    try:
        while True:
            simulate_realistic_heart_rate()
            time.sleep(1)
    except KeyboardInterrupt:
        print("Script terminated by user.")
