import os
import json
import asyncio
import sys
import tkinter as tk
from tkinter import ttk, scrolledtext
from bleak import BleakScanner, BleakClient
from pythonosc import udp_client
import threading
import base64
from io import BytesIO
from PIL import Image, ImageTk
import requests
from urllib.parse import urlencode, urlparse
from http.server import BaseHTTPRequestHandler, HTTPServer
import webbrowser
from websockets import connect
import logging
import traceback

# Setup the APPDATA_DIR and LOG_FILE paths
APPDATA_DIR = os.path.join(os.getenv('APPDATA'), 'imlunauwu')
if not os.path.exists(APPDATA_DIR):
    os.makedirs(APPDATA_DIR)

CONFIG_FILE = os.path.join(APPDATA_DIR, "config_LunaHR.json")
ICON_FILE = "icon_base64.txt"
LOG_FILE = os.path.join(APPDATA_DIR, "app.log")
HEART_RATE_UUID = "00002a37-0000-1000-8000-00805f9b34fb"

# Clear the log file on each startup
with open(LOG_FILE, 'w') as f:
    f.write('')

# Redirect stdout and stderr to the log file
sys.stdout = open(LOG_FILE, 'a')
sys.stderr = open(LOG_FILE, 'a')

# Configure logging
logging.basicConfig(filename=LOG_FILE, level=logging.DEBUG, 
                    format="%(asctime)s %(levelname)s: %(message)s")

CLIENT_ID = "0531e0ef-b030-47d5-9066-205475f01d59"
REDIRECT_URI = "http://localhost:4001/response"
SCOPE = "data:heart_rate:read"
AUTHORIZATION_URL = "https://pulsoid.net/oauth2/authorize"
VALIDATION_URL = "https://dev.pulsoid.net/api/v1/token/validate"

class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LunaHR by Luna")
        self.root.configure(bg="#2e2e2e")
        self.root.resizable(False, False)

        icon_data = self.load_icon_data()
        icon_image = Image.open(BytesIO(icon_data))
        self.icon = ImageTk.PhotoImage(icon_image)
        self.root.iconphoto(False, self.icon)

        self.main_frame = tk.Frame(root, bg="#2e2e2e")
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.control_frame = tk.Frame(self.main_frame, bg="#2e2e2e")
        self.control_frame.pack(fill=tk.X)

        self.version_label = tk.Label(self.control_frame, text="Select Version:", bg="#2e2e2e", fg="#ffffff")
        self.version_label.grid(row=0, column=0, sticky="e")
        self.version_var = tk.StringVar(value="Pulsoid")
        self.version_menu = ttk.Combobox(self.control_frame, textvariable=self.version_var, values=["Pulsoid", "Polar H10"], state="readonly")
        self.version_menu.grid(row=0, column=1, padx=10, pady=5)

        self.start_button = tk.Button(self.control_frame, text="Start", command=self.toggle_script, bg="#3b3b3b", fg="#ffffff")
        self.start_button.grid(row=0, column=2, padx=10)

        self.save_button = tk.Button(self.control_frame, text="Save Config", command=self.save_config, bg="#3b3b3b", fg="#ffffff")
        self.save_button.grid(row=0, column=3, padx=10)

        self.credit_button = tk.Button(self.control_frame, text="❤", command=self.open_author_link, bg="#3b3b3b", fg="#ffffff")
        self.credit_button.grid(row=0, column=4, padx=5)

        self.pulsoid_frame = tk.Frame(self.main_frame, bg="#2e2e2e")
        self.polar_frame = tk.Frame(self.main_frame, bg="#2e2e2e")

        self.console_frame = tk.Frame(self.main_frame, bg="#2e2e2e")
        self.console_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.console_text = scrolledtext.ScrolledText(self.console_frame, wrap=tk.WORD, width=50, height=15, bg="#1e1e1e", fg="#ffffff", insertbackground="#ffffff")
        self.console_text.pack(fill=tk.BOTH, expand=True)

        self.pulsoid_app = PulsoidOSCApp(self.pulsoid_frame, self.console_log, self.clear_console)
        self.polar_app = PolarH10OSCApp(self.polar_frame, self.console_log, self.clear_console)

        self.current_app = None

        self.load_config()
        self.switch_version(self.version_var.get())

        self.version_menu.bind("<<ComboboxSelected>>", self.on_version_change)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def load_icon_data(self):
        if hasattr(sys, '_MEIPASS'):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")

        file_path = os.path.join(base_path, ICON_FILE)
        with open(file_path, "rb") as f:
            return base64.b64decode(f.read())

    def toggle_script(self):
        try:
            if self.start_button['text'] == 'Start':
                self.start_script()
            else:
                self.stop_script()
        except Exception as e:
            logging.error(f"Error toggling script: {e}")
            traceback.print_exc()

    def start_script(self):
        try:
            if self.current_app:
                self.console_log("Starting script...")
                self.current_app.start_script()
                self.start_button.config(text="Stop")
        except Exception as e:
            logging.error(f"Error starting script: {e}")
            traceback.print_exc()

    def stop_script(self):
        try:
            if self.current_app:
                self.console_log("Stopping script...")
                self.current_app.stop_script()
                self.start_button.config(text="Start")
        except Exception as e:
            logging.error(f"Error stopping script: {e}")
            traceback.print_exc()

    def save_config(self):
        try:
            config = {
                "version": self.version_var.get(),
                "pulsoid_config": self.pulsoid_app.get_config(),
                "polar_config": self.polar_app.get_config(),
            }
            with open(CONFIG_FILE, "w") as f:
                json.dump(config, f)
            self.console_log("Configuration saved.")
        except Exception as e:
            logging.error(f"Error saving config: {e}")
            traceback.print_exc()

    def load_config(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "r") as f:
                    config = json.load(f)
                    self.version_var.set(config.get("version", "Pulsoid"))
                    self.pulsoid_app.load_config(config.get("pulsoid_config", {}))
                    self.polar_app.load_config(config.get("polar_config", {}))
            else:
                self.pulsoid_app.load_config({})
                self.polar_app.load_config({})
        except Exception as e:
            logging.error(f"Error loading config: {e}")
            traceback.print_exc()

    def switch_version(self, version):
        try:
            if self.current_app:
                self.current_app.stop_script()
                self.current_app.frame.pack_forget()
                self.clear_console()

            if version == "Pulsoid":
                self.current_app = self.pulsoid_app
                self.console_log(f"Switched to {version}")
                self.current_app.validate_token()
            elif version == "Polar H10":
                self.current_app = self.polar_app
                self.console_log(f"Switched to {version}")

            self.current_app.frame.pack(fill=tk.BOTH, expand=True, pady=10)

            if self.current_app.startup_checkbox_var.get():
                self.console_log("Start HR Tracker on Startup is enabled. Starting script automatically...")
                self.start_script()
        except Exception as e:
            logging.error(f"Error switching version: {e}")
            traceback.print_exc()

    def on_version_change(self, event=None):
        try:
            self.switch_version(self.version_var.get())
        except Exception as e:
            logging.error(f"Error on version change: {e}")
            traceback.print_exc()

    def on_closing(self):
        try:
            if self.current_app:
                self.current_app.stop_script()
            self.save_config()
            self.root.destroy()
        except Exception as e:
            logging.error(f"Error during closing: {e}")
            traceback.print_exc()

    def console_log(self, message):
        self.console_text.insert(tk.END, f"{message}\n")
        self.console_text.see(tk.END)

    def clear_console(self):
        self.console_text.delete(1.0, tk.END)

    def open_author_link(self):
        try:
            webbrowser.open("https://imluna.dev/")
        except Exception as e:
            logging.error(f"Error opening author link: {e}")
            traceback.print_exc()

class PulsoidOSCApp:
    def __init__(self, root, console_log, clear_console):
        self.frame = root
        self.console_log = console_log
        self.clear_console = clear_console
        self.frame.configure(bg="#2e2e2e")
        self.auth_token = None
        self.osc_client = None
        self.stop_flag = threading.Event()
        self.websocket_task = None
        self.loop = None
        self.heart_rates = []
        self.token_validated = False

        self.create_ui()

    def create_ui(self):
        try:
            self.vrchat_ip_label = tk.Label(self.frame, text="VRChat IP:", bg="#2e2e2e", fg="#ffffff")
            self.vrchat_ip_label.grid(row=0, column=0, sticky="e")
            self.vrchat_ip_entry = tk.Entry(self.frame, bg="#3b3b3b", fg="#ffffff", width=25)
            self.vrchat_ip_entry.grid(row=0, column=1, padx=10, pady=5)

            self.vrchat_port_label = tk.Label(self.frame, text="VRChat Port:", bg="#2e2e2e", fg="#ffffff")
            self.vrchat_port_label.grid(row=1, column=0, sticky="e")
            self.vrchat_port_entry = tk.Entry(self.frame, bg="#3b3b3b", fg="#ffffff", width=25)
            self.vrchat_port_entry.grid(row=1, column=1, padx=10, pady=5)

            self.oauth_button = tk.Button(self.frame, text="Login with Pulsoid", command=self.start_oauth_flow, bg="#3b3b3b", fg="#ffffff")
            self.oauth_button.grid(row=2, column=0, columnspan=2, pady=5)

            self.startup_checkbox_var = tk.BooleanVar()
            self.startup_checkbox = tk.Checkbutton(self.frame, text="Start HR Tracker on Startup", variable=self.startup_checkbox_var, bg="#2e2e2e", fg="#ffffff", selectcolor="#3b3b3b")
            self.startup_checkbox.grid(row=3, column=0, columnspan=2, pady=5)

            self.center_frame(self.frame)
        except Exception as e:
            logging.error(f"Error creating UI: {e}")
            traceback.print_exc()

    def center_frame(self, frame):
        try:
            for widget in frame.winfo_children():
                widget.grid_configure(sticky="ew")

            frame.grid_columnconfigure(0, weight=1)
            frame.grid_columnconfigure(1, weight=1)
        except Exception as e:
            logging.error(f"Error centering frame: {e}")
            traceback.print_exc()

    def validate_token(self):
        try:
            if not self.token_validated:
                if not self.auth_token:
                    self.token_validated = True
                    return

                headers = {"Authorization": f"Bearer {self.auth_token}"}
                try:
                    response = requests.get(VALIDATION_URL, headers=headers)
                    response_data = response.json()

                    if response.status_code == 200 and "client_id" in response_data:
                        self.console_log("Pulsoid token is valid.")
                        self.oauth_button.config(text="Logged In", font=('Helvetica', 10, 'bold'))
                    else:
                        self.console_log("Invalid Pulsoid token. Please log in again.")
                        self.auth_token = None
                        self.oauth_button.config(text="Login with Pulsoid", font=('Helvetica', 10))

                except requests.exceptions.RequestException as e:
                    self.console_log(f"Error validating token: {e}")
                    self.auth_token = None
                    self.oauth_button.config(text="Login with Pulsoid", font=('Helvetica', 10))

                self.token_validated = True
        except Exception as e:
            logging.error(f"Error validating token: {e}")
            traceback.print_exc()

    def get_config(self):
        try:
            return {
                "vrchat_ip": self.vrchat_ip_entry.get(),
                "vrchat_port": self.vrchat_port_entry.get(),
                "auth_token": self.auth_token,
                "start_on_startup": self.startup_checkbox_var.get()
            }
        except Exception as e:
            logging.error(f"Error getting config: {e}")
            traceback.print_exc()

    def load_config(self, config):
        try:
            self.vrchat_ip_entry.delete(0, tk.END)
            self.vrchat_port_entry.delete(0, tk.END)

            self.vrchat_ip_entry.insert(0, config.get("vrchat_ip", "127.0.0.1"))
            self.vrchat_port_entry.insert(0, config.get("vrchat_port", "9000"))
            self.auth_token = config.get("auth_token", None)
            self.startup_checkbox_var.set(config.get("start_on_startup", False))

            if self.auth_token:
                self.validate_token()
        except Exception as e:
            logging.error(f"Error loading config: {e}")
            traceback.print_exc()

    def start_oauth_flow(self):
        try:
            params = {
                "client_id": CLIENT_ID,
                "response_type": "token",
                "redirect_uri": REDIRECT_URI,
                "scope": SCOPE,
                "state": "some_random_state"
            }
            auth_url = f"{AUTHORIZATION_URL}?{urlencode(params)}"
            webbrowser.open(auth_url)

            server = HTTPServer(('localhost', 4001), OAuthServerHandler)
            server.timeout = 60
            while not hasattr(server, 'auth_token'):
                server.handle_request()

            auth_token = server.auth_token

            if not auth_token:
                self.console_log("Authorization failed. No auth token received.")
                return

            self.auth_token = auth_token
            self.oauth_button.config(text="Logged In", font=('Helvetica', 10, 'bold'))
            self.console_log("Authorization successful.")
        except Exception as e:
            logging.error(f"Error in OAuth flow: {e}")
            traceback.print_exc()

    def start_script(self):
        try:
            vrchat_ip = self.vrchat_ip_entry.get()
            vrchat_port = int(self.vrchat_port_entry.get())

            if not self.auth_token:
                self.console_log("Please log in with Pulsoid first.")
                return

            self.osc_client = udp_client.SimpleUDPClient(vrchat_ip, vrchat_port)
            self.stop_flag.clear()
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.websocket_task = self.loop.create_task(self.run_websocket(self.auth_token))
            threading.Thread(target=self.loop.run_forever).start()
        except Exception as e:
            logging.error(f"Error starting script: {e}")
            traceback.print_exc()

    def stop_script(self):
        try:
            self.stop_flag.set()
            if self.websocket_task:
                self.websocket_task.cancel()
            if self.loop:
                self.loop.call_soon_threadsafe(self.loop.stop)
            
            if self.heart_rates:
                average_hr = sum(self.heart_rates) / len(self.heart_rates)
                self.console_log(f"Average Heart Rate: {average_hr:.2f} BPM")
            else:
                self.console_log("No heart rate data collected.")
        except Exception as e:
            logging.error(f"Error stopping script: {e}")
            traceback.print_exc()

    async def run_websocket(self, token):
        try:
            ws_url = f"wss://dev.pulsoid.net/api/v1/data/real_time?access_token={token}"
            async with connect(ws_url) as websocket:
                while not self.stop_flag.is_set():
                    try:
                        message = await websocket.recv()
                        json_data = json.loads(message)
                        heart_rate = json_data["data"]["heart_rate"]
                        self.console_log(f"Heart Rate: {heart_rate} BPM")
                        self.heart_rates.append(heart_rate)
                        self.send_heart_rate_osc(heart_rate)
                    except json.JSONDecodeError:
                        self.console_log("Error decoding JSON data.")
                    except KeyError:
                        self.console_log("Error accessing data fields.")
                    except asyncio.CancelledError:
                        break
        except Exception as e:
            logging.error(f"Error in WebSocket connection: {e}")
            traceback.print_exc()

    def send_heart_rate_osc(self, heart_rate):
        try:
            ones_hr = heart_rate % 10
            tens_hr = (heart_rate // 10) % 10
            hundreds_hr = (heart_rate // 100) % 10

            self.osc_client.send_message("/avatar/parameters/hr/ones_hr", ones_hr)
            self.osc_client.send_message("/avatar/parameters/hr/tens_hr", tens_hr)
            self.osc_client.send_message("/avatar/parameters/hr/hundreds_hr", hundreds_hr)
            self.osc_client.send_message("/avatar/parameters/hr/heart_rate", heart_rate)
        except Exception as e:
            logging.error(f"Error sending heart rate OSC: {e}")
            traceback.print_exc()

class PolarH10OSCApp:
    def __init__(self, root, console_log, clear_console):
        self.frame = root
        self.console_log = console_log
        self.clear_console = clear_console
        self.frame.configure(bg="#2e2e2e")
        self.osc_client = None
        self.stop_flag = threading.Event()
        self.loop = None
        self.thread = None
        self.heart_rates = []

        self.create_ui()

    def create_ui(self):
        try:
            self.vrchat_ip_label = tk.Label(self.frame, text="VRChat IP:", bg="#2e2e2e", fg="#ffffff")
            self.vrchat_ip_label.grid(row=0, column=0, sticky="e")
            self.vrchat_ip_entry = tk.Entry(self.frame, bg="#3b3b3b", fg="#ffffff", width=25)
            self.vrchat_ip_entry.grid(row=0, column=1, padx=10, pady=5)

            self.vrchat_port_label = tk.Label(self.frame, text="VRChat Port:", bg="#2e2e2e", fg="#ffffff")
            self.vrchat_port_label.grid(row=1, column=0, sticky="e")
            self.vrchat_port_entry = tk.Entry(self.frame, bg="#3b3b3b", fg="#ffffff", width=25)
            self.vrchat_port_entry.grid(row=1, column=1, padx=10, pady=5)

            self.polar_h10_name_label = tk.Label(self.frame, text="Polar H10 Name:", bg="#2e2e2e", fg="#ffffff")
            self.polar_h10_name_label.grid(row=2, column=0, sticky="e")
            self.polar_h10_name_entry = tk.Entry(self.frame, bg="#3b3b3b", fg="#ffffff", width=25)
            self.polar_h10_name_entry.grid(row=2, column=1, padx=10, pady=5)

            self.startup_checkbox_var = tk.BooleanVar()
            self.startup_checkbox = tk.Checkbutton(self.frame, text="Start HR Tracker on Startup", variable=self.startup_checkbox_var, bg="#2e2e2e", fg="#ffffff", selectcolor="#3b3b3b")
            self.startup_checkbox.grid(row=3, column=0, columnspan=2, pady=5)

            self.center_frame(self.frame)
        except Exception as e:
            logging.error(f"Error creating UI: {e}")
            traceback.print_exc()

    def center_frame(self, frame):
        try:
            for widget in frame.winfo_children():
                widget.grid_configure(sticky="ew")

            frame.grid_columnconfigure(0, weight=1)
            frame.grid_columnconfigure(1, weight=1)
        except Exception as e:
            logging.error(f"Error centering frame: {e}")
            traceback.print_exc()

    def get_config(self):
        try:
            return {
                "vrchat_ip": self.vrchat_ip_entry.get(),
                "vrchat_port": self.vrchat_port_entry.get(),
                "polar_h10_name": self.polar_h10_name_entry.get(),
                "start_on_startup": self.startup_checkbox_var.get()
            }
        except Exception as e:
            logging.error(f"Error getting config: {e}")
            traceback.print_exc()

    def load_config(self, config):
        try:
            self.vrchat_ip_entry.delete(0, tk.END)
            self.vrchat_port_entry.delete(0, tk.END)
            self.polar_h10_name_entry.delete(0, tk.END)

            self.vrchat_ip_entry.insert(0, config.get("vrchat_ip", "127.0.0.1"))
            self.vrchat_port_entry.insert(0, config.get("vrchat_port", "9000"))
            self.polar_h10_name_entry.insert(0, config.get("polar_h10_name", "Polar H10 B71CC122"))
            self.startup_checkbox_var.set(config.get("start_on_startup", False))
        except Exception as e:
            logging.error(f"Error loading config: {e}")
            traceback.print_exc()

    def start_script(self):
        try:
            vrchat_ip = self.vrchat_ip_entry.get()
            vrchat_port = int(self.vrchat_port_entry.get())
            polar_h10_name = self.polar_h10_name_entry.get()

            self.osc_client = udp_client.SimpleUDPClient(vrchat_ip, vrchat_port)
            self.stop_flag.clear()
            self.loop = asyncio.new_event_loop()
            self.thread = threading.Thread(target=self.run_async_script, args=(polar_h10_name,))
            self.thread.start()
        except Exception as e:
            logging.error(f"Error starting script: {e}")
            traceback.print_exc()

    def stop_script(self):
        try:
            self.stop_flag.set()
            if self.loop:
                self.loop.call_soon_threadsafe(self.loop.stop)
            if self.thread:
                self.thread.join()

            if self.heart_rates:
                average_hr = sum(self.heart_rates) / len(self.heart_rates)
                self.console_log(f"Average Heart Rate: {average_hr:.2f} BPM")
            else:
                self.console_log("No heart rate data collected.")
        except Exception as e:
            logging.error(f"Error stopping script: {e}")
            traceback.print_exc()

    def run_async_script(self, polar_h10_name):
        try:
            asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(self.run_script(polar_h10_name))
            self.loop.close()
        except Exception as e:
            logging.error(f"Error in async script: {e}")
            traceback.print_exc()

    async def run_script(self, polar_h10_name):
        try:
            retry_interval = 10
            while not self.stop_flag.is_set():
                try:
                    devices = await BleakScanner.discover()
                    polar_h10_device = None
                    for device in devices:
                        if device.name and polar_h10_name in device.name:
                            polar_h10_device = device
                            break

                    if polar_h10_device:
                        self.console_log(f"Found Polar H10: {polar_h10_device}")
                        async with BleakClient(polar_h10_device.address) as client:
                            await client.start_notify(HEART_RATE_UUID, self.handle_heart_rate)
                            try:
                                while not self.stop_flag.is_set():
                                    await asyncio.sleep(1)
                            except KeyboardInterrupt:
                                self.console_log("Exiting gracefully.")
                                await client.stop_notify(HEART_RATE_UUID)
                                break
                    else:
                        self.console_log(f"Polar H10 not found. Retrying in {retry_interval} seconds.")
                        await asyncio.sleep(retry_interval)

                except Exception as e:
                    self.console_log(f"Error: {e}. Retrying in {retry_interval} seconds.")
                    await asyncio.sleep(retry_interval)
        except Exception as e:
            logging.error(f"Error in WebSocket script: {e}")
            traceback.print_exc()

    def handle_heart_rate(self, sender: int, data: bytearray):
        try:
            heart_rate = data[1]
            self.console_log(f"Heart Rate: {heart_rate} BPM")
            
            self.heart_rates.append(heart_rate)

            ones_hr = heart_rate % 10
            tens_hr = (heart_rate // 10) % 10
            hundreds_hr = (heart_rate // 100) % 10
            self.osc_client.send_message("/avatar/parameters/hr/ones_hr", ones_hr)
            self.osc_client.send_message("/avatar/parameters/hr/tens_hr", tens_hr)
            self.osc_client.send_message("/avatar/parameters/hr/hundreds_hr", hundreds_hr)
            self.osc_client.send_message("/avatar/parameters/hr/heart_rate", heart_rate)
        except Exception as e:
            logging.error(f"Error handling heart rate: {e}")
            traceback.print_exc()

class OAuthServerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            if self.path.startswith('/response'):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                html_content = """
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <title>OAuth Callback</title>
                </head>
                <body>
                    <script type="text/javascript">
                        const fragment = window.location.hash.substring(1);
                        const params = new URLSearchParams(fragment);
                        const accessToken = params.get('access_token');
                        
                        if (accessToken) {
                            window.location.href = "/store_token?access_token=" + accessToken;
                        } else {
                            document.body.innerText = "Authorization failed. No access token received.";
                        }
                    </script>
                </body>
                </html>
                """
                self.wfile.write(html_content.encode('utf-8'))

            elif self.path.startswith('/store_token'):
                query = urlparse(self.path).query
                params = {}
                for param in query.split('&'):
                    if '=' in param:
                        key, value = param.split('=', 1)
                        params[key] = value

                if "access_token" in params:
                    self.server.auth_token = params["access_token"]
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b"Authorization successful. You can close this window.")
                else:
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(b"Authorization failed. No access token received.")
        except Exception as e:
            logging.error(f"Error in OAuthServerHandler: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = MainApp(root)
        root.mainloop()
    except Exception as e:
        logging.error(f"Error in main application: {e}")
        traceback.print_exc()
