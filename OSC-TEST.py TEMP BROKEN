import subprocess

def install_dependencies():
    required_packages = ["python-osc"]

    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            print(f"Installing {package}...")
            subprocess.check_call(["pip", "install", package])

def receive_heart_rate(unused_addr, onesHR, tensHR, hundredsHR, HR):
    print(f"Ones HR: {onesHR}, Tens HR: {tensHR}, Hundreds HR: {hundredsHR}, Raw HR: {HR}")

if __name__ == "__main__":
    install_dependencies()
    from pythonosc import dispatcher, osc_server

    server_ip = '127.0.0.1'
    server_port = 9000

    dispatcher_instance = dispatcher.Dispatcher()
    dispatcher_instance.map("/vrchat/heart_rate", receive_heart_rate)

    osc_server_instance = osc_server.ThreadingOSCUDPServer((server_ip, server_port), dispatcher_instance)

    print(f"Listening for heart rate data on {server_ip}:{server_port}")
    
    try:
        osc_server_instance.serve_forever()
    except KeyboardInterrupt:
        print("Server terminated by user.")
