import os
import json
import asyncio
import sys
import tkinter as tk
from tkinter import scrolledtext
from pythonosc import udp_client
import threading
from urllib.parse import urlencode, urlparse
from http.server import BaseHTTPRequestHandler, HTTPServer
import webbrowser
from websockets import connect
from io import BytesIO
from PIL import Image, ImageTk
import requests
import base64

APPDATA_DIR = os.path.join(os.getenv('APPDATA'), 'imlunauwu')
CONFIG_FILE = os.path.join(APPDATA_DIR, "config_Pulsoid.json")
ICON_FILE = "icon_base64.txt"

CLIENT_ID = "YOUR_CLIENT_ID"
REDIRECT_URI = "http://localhost:4001/response"
SCOPE = "data:heart_rate:read"
AUTHORIZATION_URL = "https://pulsoid.net/oauth2/authorize"
VALIDATION_URL = "https://dev.pulsoid.net/api/v1/token/validate"

DEFAULT_CONFIG = {
    "vrchat_ip": "127.0.0.1",
    "vrchat_port": "9000",
    "token": None,
    "start_on_startup": False,
}

class OAuthServerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
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
                    setTimeout(function() { window.close(); }, 5000);
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
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b"Authorization successful. You can close this window.")
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Authorization failed. No access token received.")

class PulsoidOSCApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PulsoidOSC by Luna")

        bg_color = "#2e2e2e"
        fg_color = "#ffffff"
        entry_bg_color = "#3b3b3b"
        entry_fg_color = "#ffffff"
        text_bg_color = "#1e1e1e"
        text_fg_color = "#ffffff"

        self.root.configure(bg=bg_color)
        self.root.resizable(False, False)

        icon_data = self.load_icon_data()
        icon_image = Image.open(BytesIO(icon_data))
        self.icon = ImageTk.PhotoImage(icon_image)
        self.root.iconphoto(False, self.icon)

        self.vrchat_ip_label = tk.Label(root, text="VRChat IP:", bg=bg_color, fg=fg_color)
        self.vrchat_ip_label.grid(row=0, column=0, sticky="w")
        self.vrchat_ip_entry = tk.Entry(root, bg=entry_bg_color, fg=entry_fg_color)
        self.vrchat_ip_entry.grid(row=0, column=1, padx=10, pady=5)

        self.vrchat_port_label = tk.Label(root, text="VRChat Port:", bg=bg_color, fg=fg_color)
        self.vrchat_port_label.grid(row=1, column=0, sticky="w")
        self.vrchat_port_entry = tk.Entry(root, bg=entry_bg_color, fg=entry_fg_color)
        self.vrchat_port_entry.grid(row=1, column=1, padx=10, pady=5)

        self.oauth_button = tk.Button(root, text="Login with Pulsoid", command=self.start_oauth_flow, bg=entry_bg_color, fg=entry_fg_color)
        self.oauth_button.grid(row=2, column=0, columnspan=2, pady=5)

        self.startup_checkbox_var = tk.BooleanVar()
        self.startup_checkbox = tk.Checkbutton(root, text="Start HR Tracker on Startup", variable=self.startup_checkbox_var, bg=bg_color, fg=fg_color, selectcolor=entry_bg_color)
        self.startup_checkbox.grid(row=3, column=0, columnspan=2, pady=5)

        self.start_button = tk.Button(root, text="Start", command=self.toggle_script, bg=entry_bg_color, fg=entry_fg_color)
        self.start_button.grid(row=4, column=0, pady=10)

        self.save_button = tk.Button(root, text="Save Config", command=self.save_config, bg=entry_bg_color, fg=entry_fg_color)
        self.save_button.grid(row=4, column=1, pady=10)

        self.console_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=50, height=15, bg=text_bg_color, fg=text_fg_color, insertbackground=fg_color)
        self.console_text.grid(row=5, column=0, columnspan=2, padx=10, pady=10)
        self.console_text.bind("<MouseWheel>", self.on_scroll)
        self.console_text.bind("<Button-4>", self.on_scroll)
        self.console_text.bind("<Button-5>", self.on_scroll)

        self.osc_client = None
        self.stop_flag = threading.Event()
        self.auto_scroll_enabled = True
        self.websocket_task = None
        self.auth_token = None

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.load_config()

        if self.auth_token:
            self.validate_token()

        if self.startup_checkbox_var.get():
            self.start_script()

    def load_icon_data(self):
        if hasattr(sys, '_MEIPASS'):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")

        file_path = os.path.join(base_path, "icon_base64.txt")
        with open(file_path, "rb") as f:
            return base64.b64decode(f.read())

    def validate_token(self):
        headers = {
            'Authorization': f'Bearer {self.auth_token}',
            'Content-Type': 'application/json',
        }
        response = requests.get(VALIDATION_URL, headers=headers)

        if response.status_code == 200:
            self.console_text.insert(tk.END, "Logged in. :3\n")
            self.oauth_button.config(text="Logged In", font=('Helvetica', 10, 'bold'))
        else:
            self.console_text.insert(tk.END, "Token is invalid or expired. Please log in again.\n")
            self.auth_token = None
            self.save_config()
            self.oauth_button.config(text="Login with Pulsoid", font=('Helvetica', 10))

        self.auto_scroll()

    def start_oauth_flow(self):
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
        while not hasattr(server, 'auth_token'):
            server.handle_request()

        auth_token = server.auth_token

        if not auth_token:
            self.console_text.insert(tk.END, "Authorization failed. No auth token received.\n")
            self.auto_scroll()
            return

        self.auth_token = auth_token
        self.console_text.insert(tk.END, "Login successful.\n")
        self.oauth_button.config(text="Logged In", font=('Helvetica', 10, 'bold'))
        self.auto_scroll()
        self.save_config()

    def load_config(self):
        if not os.path.exists(APPDATA_DIR):
            os.makedirs(APPDATA_DIR)

        config = DEFAULT_CONFIG.copy()

        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                saved_config = json.load(f)
                config.update(saved_config)

        self.vrchat_ip_entry.insert(0, config.get("vrchat_ip"))
        self.vrchat_port_entry.insert(0, config.get("vrchat_port"))
        self.auth_token = config.get("token")
        self.startup_checkbox_var.set(config.get("start_on_startup", False))

    def save_config(self):
        config = {
            "vrchat_ip": self.vrchat_ip_entry.get(),
            "vrchat_port": self.vrchat_port_entry.get(),
            "token": self.auth_token,
            "start_on_startup": self.startup_checkbox_var.get()
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f)
        self.console_text.insert(tk.END, "Configuration saved.\n")
        self.auto_scroll()

    def toggle_script(self):
        if self.start_button['text'] == 'Start':
            self.start_script()
        else:
            self.stop_script()

    def start_script(self):
        vrchat_ip = self.vrchat_ip_entry.get()
        vrchat_port = int(self.vrchat_port_entry.get())

        if not self.auth_token:
            self.console_text.insert(tk.END, "Please log in with Pulsoid first.\n")
            self.auto_scroll()
            return

        self.osc_client = udp_client.SimpleUDPClient(vrchat_ip, vrchat_port)
        self.console_text.insert(tk.END, f"Starting with VRChat IP: {vrchat_ip}, Port: {vrchat_port}\n")
        self.auto_scroll()

        self.stop_flag.clear()
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.websocket_task = self.loop.create_task(self.run_websocket(self.auth_token))
        threading.Thread(target=self.loop.run_forever).start()

        self.start_button.config(text="Stop")

    def stop_script(self):
        self.console_text.insert(tk.END, "Stopping script...\n")
        self.auto_scroll()
        self.stop_flag.set()
        if self.websocket_task:
            self.websocket_task.cancel()
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)
        self.console_text.insert(tk.END, "Script stopped.\n")
        self.auto_scroll()

        self.start_button.config(text="Start")

    async def run_websocket(self, token):
        ws_url = f"wss://dev.pulsoid.net/api/v1/data/real_time?access_token={token}"

        async with connect(ws_url) as websocket:
            while not self.stop_flag.is_set():
                try:
                    message = await websocket.recv()
                    json_data = json.loads(message)
                    heart_rate = json_data["data"]["heart_rate"]
                    self.console_text.insert(tk.END, f"Heart Rate: {heart_rate}\n")
                    self.auto_scroll()
                    self.send_heart_rate_osc(heart_rate)
                except json.JSONDecodeError:
                    pass
                except KeyError:
                    pass
                except asyncio.CancelledError:
                    break

    def send_heart_rate_osc(self, heart_rate):
        ones_hr = heart_rate % 10
        tens_hr = (heart_rate // 10) % 10
        hundreds_hr = (heart_rate // 100) % 10

        self.osc_client.send_message("/avatar/parameters/hr/ones_hr", ones_hr)
        self.osc_client.send_message("/avatar/parameters/hr/tens_hr", tens_hr)
        self.osc_client.send_message("/avatar/parameters/hr/hundreds_hr", hundreds_hr)
        self.osc_client.send_message("/avatar/parameters/hr/heart_rate", heart_rate)

    def auto_scroll(self):
        if self.auto_scroll_enabled:
            self.console_text.yview(tk.END)

    def on_scroll(self, event):
        self.auto_scroll_enabled = self.is_scrolled_to_bottom()

    def is_scrolled_to_bottom(self):
        return self.console_text.yview()[1] >= 1.0

    def on_closing(self):
        self.console_text.insert(tk.END, "Closing application...\n")
        self.auto_scroll()
        if self.start_button['text'] == 'Stop':
            self.stop_script()
        self.save_config()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = PulsoidOSCApp(root)
    root.mainloop()
