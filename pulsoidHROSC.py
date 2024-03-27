import subprocess
import websocket
import json
from pythonosc import udp_client

# Install websocket-client and python-osc dependencies
try:
    import websocket
    from pythonosc import udp_client
except ImportError:
    print("Installing websocket-client and python-osc...")
    subprocess.call(['pip', 'install', 'websocket-client', 'python-osc'])
    import websocket
    from pythonosc import udp_client

# Define the Pulsoid access token
token = "YOUR_ACCESS_TOKEN_HERE"

# Replace the following values with your VRChat IP and port
vrchat_ip = "127.0.0.1"
vrchat_port = 9000

osc_client = udp_client.SimpleUDPClient(vrchat_ip, vrchat_port)

def send_heart_rate_osc(heart_rate):
    ones_hr = heart_rate % 10
    tens_hr = (heart_rate // 10) % 10
    hundreds_hr = (heart_rate // 100) % 10

    osc_client.send_message("/avatar/parameters/hr/ones_hr", ones_hr)
    osc_client.send_message("/avatar/parameters/hr/tens_hr", tens_hr)
    osc_client.send_message("/avatar/parameters/hr/hundreds_hr", hundreds_hr)
    osc_client.send_message("/avatar/parameters/hr/heart_rate", heart_rate)

def on_message(ws, message):
    try:
        json_data = json.loads(message)
        heart_rate = json_data["data"]["heart_rate"]
        print(f"Heart Rate: {heart_rate}")
        send_heart_rate_osc(heart_rate)
    except json.JSONDecodeError:
        pass
    except KeyError:
        pass


def on_error(ws, error):
    print("### there was an error, please check configuration ###")
    print("### if this script was just closed using keyboard interrupt, this can safely be ignored ###")

def on_close(ws):
    print("### websocket closed ###")

def on_open(ws):
    print("### connected ###")

if __name__ == "__main__":
    websocket.enableTrace(False) 

    ws_url = f"wss://dev.pulsoid.net/api/v1/data/real_time?access_token={token}"

    ws = websocket.WebSocketApp(ws_url,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    ws.on_open = on_open

    try:
        ws.run_forever()
    except KeyboardInterrupt:
        pass

