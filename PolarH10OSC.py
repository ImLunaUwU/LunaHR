import os
import json
import asyncio
import sys
import tkinter as tk
from tkinter import scrolledtext
from bleak import BleakScanner, BleakClient
from pythonosc import udp_client
import threading
import base64
from io import BytesIO
from PIL import Image, ImageTk

APPDATA_DIR = os.path.join(os.getenv('APPDATA'), 'imlunauwu')
CONFIG_FILE = os.path.join(APPDATA_DIR, "config_PolarH10.json")
HEART_RATE_UUID = "00002a37-0000-1000-8000-00805f9b34fb"
ICON_FILE = "icon_base64.txt"

class PolarH10OSCApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PolarH10OSC by Luna")

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

        self.polar_h10_name_label = tk.Label(root, text="Polar H10 Name:", bg=bg_color, fg=fg_color)
        self.polar_h10_name_label.grid(row=2, column=0, sticky="w")
        self.polar_h10_name_entry = tk.Entry(root, bg=entry_bg_color, fg=entry_fg_color)
        self.polar_h10_name_entry.grid(row=2, column=1, padx=10, pady=5)

        self.startup_checkbox_var = tk.BooleanVar()
        self.startup_checkbox = tk.Checkbutton(root, text="Start HR Tracker on Startup", variable=self.startup_checkbox_var, bg=bg_color, fg=fg_color, selectcolor=entry_bg_color)
        self.startup_checkbox.grid(row=3, column=0, columnspan=2, pady=5)

        self.load_config()

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
        self.stop_flag = False
        self.thread = None
        self.loop = None
        self.auto_scroll_enabled = True

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

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

    def load_config(self):
        if not os.path.exists(APPDATA_DIR):
            os.makedirs(APPDATA_DIR)
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
                self.vrchat_ip_entry.insert(0, config.get("vrchat_ip", "127.0.0.1"))
                self.vrchat_port_entry.insert(0, config.get("vrchat_port", "9910"))
                self.polar_h10_name_entry.insert(0, config.get("polar_h10_name", "Polar H10 B71CC122"))
                self.startup_checkbox_var.set(config.get("start_on_startup", False))
        else:
            self.vrchat_ip_entry.insert(0, "127.0.0.1")
            self.vrchat_port_entry.insert(0, "9910")
            self.polar_h10_name_entry.insert(0, "Polar H10 B71CC122")

    def save_config(self):
        config = {
            "vrchat_ip": self.vrchat_ip_entry.get(),
            "vrchat_port": self.vrchat_port_entry.get(),
            "polar_h10_name": self.polar_h10_name_entry.get(),
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
        polar_h10_name = self.polar_h10_name_entry.get()

        self.osc_client = udp_client.SimpleUDPClient(vrchat_ip, vrchat_port)
        self.console_text.insert(tk.END, f"Starting with VRChat IP: {vrchat_ip}, Port: {vrchat_port}, Polar H10 Name: {polar_h10_name}\n")
        self.auto_scroll()

        self.stop_flag = False
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.run_async_script, args=(polar_h10_name,))
        self.thread.start()

        self.start_button.config(text="Stop")

    def stop_script(self):
        self.stop_flag = True
        if self.thread is not None:
            self.loop.call_soon_threadsafe(self.loop.stop)
            self.thread.join()
        self.console_text.insert(tk.END, "HR listener stopped.\n")
        self.auto_scroll()

        self.start_button.config(text="Start")

    def run_async_script(self, polar_h10_name):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.run_script(polar_h10_name))
        self.loop.close()

    async def run_script(self, polar_h10_name):
        retry_interval = 10
        while not self.stop_flag:
            try:
                devices = await BleakScanner.discover()
                polar_h10_device = None
                for device in devices:
                    if device.name and polar_h10_name in device.name:
                        polar_h10_device = device
                        break

                if polar_h10_device:
                    self.console_text.insert(tk.END, f"Found Polar H10: {polar_h10_device}\n")
                    self.auto_scroll()
                    async with BleakClient(polar_h10_device.address) as client:
                        await client.start_notify(HEART_RATE_UUID, self.handle_heart_rate)

                        try:
                            while not self.stop_flag:
                                await asyncio.sleep(1)
                        except KeyboardInterrupt:
                            self.console_text.insert(tk.END, "Exiting gracefully.\n")
                            await client.stop_notify(HEART_RATE_UUID)
                            break

                else:
                    self.console_text.insert(tk.END, f"Polar H10 not found. Retrying in {retry_interval} seconds.\n")
                    self.auto_scroll()
                    await asyncio.sleep(retry_interval)

            except Exception as e:
                self.console_text.insert(tk.END, f"Error: {e}. Retrying in {retry_interval} seconds.\n")
                self.auto_scroll()
                await asyncio.sleep(retry_interval)

    def handle_heart_rate(self, sender: int, data: bytearray):
        heart_rate = data[1]
        self.console_text.insert(tk.END, f"Heart Rate: {heart_rate}\n")
        self.auto_scroll()

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
    app = PolarH10OSCApp(root)
    root.mainloop()
