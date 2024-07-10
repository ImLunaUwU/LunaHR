import subprocess
import sys
import os
import json
import asyncio
import tkinter as tk
from tkinter import scrolledtext
from pythonosc import udp_client
import threading
import base64
from io import BytesIO
from PIL import Image, ImageTk
from websocket import WebSocketApp

APPDATA_DIR = os.path.join(os.getenv('APPDATA'), 'imlunauwu')
CONFIG_FILE = os.path.join(APPDATA_DIR, "config_Pulsoid.json")

icon_base64 = """
<your_base64_encoded_string_here>
"""

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

        icon_data = base64.b64decode(icon_base64)
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

        self.token_label = tk.Label(root, text="Pulsoid Token:", bg=bg_color, fg=fg_color)
        self.token_label.grid(row=2, column=0, sticky="w")
        self.token_entry = tk.Entry(root, bg=entry_bg_color, fg=entry_fg_color)
        self.token_entry.grid(row=2, column=1, padx=10, pady=5)

        self.load_config()

        self.start_button = tk.Button(root, text="Start", command=self.toggle_script, bg=entry_bg_color, fg=entry_fg_color)
        self.start_button.grid(row=3, column=0, pady=10)

        self.save_button = tk.Button(root, text="Save Config", command=self.save_config, bg=entry_bg_color, fg=entry_fg_color)
        self.save_button.grid(row=3, column=1, pady=10)

        self.console_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=50, height=15, bg=text_bg_color, fg=text_fg_color, insertbackground=fg_color)
        self.console_text.grid(row=4, column=0, columnspan=2, padx=10, pady=10)
        self.console_text.bind("<MouseWheel>", self.on_scroll)
        self.console_text.bind("<Button-4>", self.on_scroll)
        self.console_text.bind("<Button-5>", self.on_scroll)

        self.osc_client = None
        self.stop_flag = threading.Event()
        self.thread = None
        self.ws = None
        self.auto_scroll_enabled = True

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def load_config(self):
        if not os.path.exists(APPDATA_DIR):
            os.makedirs(APPDATA_DIR)
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
                self.vrchat_ip_entry.insert(0, config.get("vrchat_ip", "127.0.0.1"))
                self.vrchat_port_entry.insert(0, config.get("vrchat_port", "9000"))
                self.token_entry.insert(0, config.get("token", "YOUR_ACCESS_TOKEN_HERE"))
        else:
            self.vrchat_ip_entry.insert(0, "127.0.0.1")
            self.vrchat_port_entry.insert(0, "9000")
            self.token_entry.insert(0, "YOUR_ACCESS_TOKEN_HERE")

    def save_config(self):
        config = {
            "vrchat_ip": self.vrchat_ip_entry.get(),
            "vrchat_port": self.vrchat_port_entry.get(),
            "token": self.token_entry.get(),
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
        token = self.token_entry.get()

        self.osc_client = udp_client.SimpleUDPClient(vrchat_ip, vrchat_port)
        self.console_text.insert(tk.END, f"Starting with VRChat IP: {vrchat_ip}, Port: {vrchat_port}, Token: {token}\n")
        self.auto_scroll()

        self.stop_flag.clear()
        self.thread = threading.Thread(target=self.run_websocket, args=(token,))
        self.thread.start()

        self.start_button.config(text="Stop")

    def stop_script(self):
        self.stop_flag.set()
        if self.ws:
            self.ws.close()
        if self.thread is not None:
            self.thread.join()
        self.console_text.insert(tk.END, "Script stopped.\n")
        self.auto_scroll()

        self.start_button.config(text="Start")

    def run_websocket(self, token):
        ws_url = f"wss://dev.pulsoid.net/api/v1/data/real_time?access_token={token}"

        def on_message(ws, message):
            try:
                json_data = json.loads(message)
                heart_rate = json_data["data"]["heart_rate"]
                self.console_text.insert(tk.END, f"Heart Rate: {heart_rate}\n")
                self.auto_scroll()
                self.send_heart_rate_osc(heart_rate)
            except json.JSONDecodeError:
                pass
            except KeyError:
                pass

        def on_error(ws, error):
            self.console_text.insert(tk.END, f"### Error: {error} ###\n")
            self.auto_scroll()

        def on_close(ws, close_status_code, close_msg):
            self.console_text.insert(tk.END, "### websocket closed ###\n")
            self.auto_scroll()

        def on_open(ws):
            self.console_text.insert(tk.END, "### connected ###\n")
            self.auto_scroll()

        def run():
            asyncio.set_event_loop(asyncio.new_event_loop())
            self.ws = WebSocketApp(ws_url,
                                   on_message=on_message,
                                   on_error=on_error,
                                   on_close=on_close)
            self.ws.on_open = on_open
            self.ws.run_forever()

        ws_thread = threading.Thread(target=run)
        ws_thread.start()

        self.stop_flag.wait()
        if self.ws:
            self.ws.close()
        ws_thread.join()

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
        if self.start_button['text'] == 'Stop':
            self.stop_script()
        self.save_config()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = PulsoidOSCApp(root)
    root.mainloop()
