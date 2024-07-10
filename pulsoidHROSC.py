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
from websockets import connect

APPDATA_DIR = os.path.join(os.getenv('APPDATA'), 'imlunauwu')
CONFIG_FILE = os.path.join(APPDATA_DIR, "config_Pulsoid.json")

icon_base64 = """
iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAMAAAAoLQ9TAAAAIGNIUk0AAHomAACAhAAA+gAAAIDoAAB1MAAA6mAAADqYAAAXcJy6UTwAAALfUExURdmls9mjsdmot9mrutiottisutipuNiisdeisdagsNamttequdeouNahsdWer9SesNqksdqqt9eToNNga9JRW9NeadaHlNqjsNqottaOnNR5hdaCj9merdiks9edrdiptdWEkM81Ps8vN88xOc8uNs8tNtNve9aottJibtA0PdFDTdaIldihr9icp9FCS88tNc84Qc81PdBLVc8zO9A5Qs84QM4uN9FASdWTodOCjs8uN9JMVtNnctA3QM80Pc8yO9A6Q89AStBETtAyO9A1Ps8sNNJqds5ndNJOWNi0wdelstecqdAtNtFFT9iqt9mqt9KmtMpvfdJCS9ejsNeotdFJU89PWsxpddeWotN4g84dJNims9BpddWQnNR9iM5DTdXBz8V/kNWir9Nxe9Nsd9eapspTYMaBj9avvNJUXs8lLdd9iMytvdKvvdRGT8BcbM6vvsidrtSpt9MvNtMzO9ekscB6jLl+kdO0wsGHmLhvgMyaqMumtdKpt8xbZ7Nxg86frsejtM+mtbpbbb1eb9Gsu7V/lbNyhtCywcl3hLw/Tc91gtOksrJ+k7FSZdmdqMx9i8+qua9XbLRqf8+xwKpshatne7yPoNqlsdpueNmvu9eBi8GqvcV+jtmksM8xOtdjbNqDjb2brptbdaJlep5edLSJnLymt8xVYNMtNcs7RtKJldiapc9LVdArM9NRW8isvL2er5Ved5FbdZRacJJZbotPZYVMY5NKX8k7RdUzOswtNcwsNNQwN805QpxEVoFOZoJNZ4RSbIRUbodSaINPZoNQZoBOZXhOZoNLYbw8SNk2PtY2Prs8SIVJXXdNZHtLYXpMZHlMZXxOZ35MYXRHXndIXnFFXHFEWnBGW2lDWqE8S6I+TG5GW25FWnNEWW9EW29FW3BFXXBGXmtCWHFEWW5DV2lAVGY/U2U+UmE9UVo9U10/VGQ+Umg/U2c/VGM+VGE9VGVAVmlBWP///50aps8AAAABYktHRPQy1StNAAAAB3RJTUUH6AcKDx4Lo5GuUQAAARtJREFUGNMBEAHv/gAAAQIDBAUGBwgJCgsMDQ4PABAREhMUFRYEFxgZGhscHR4AHyAhIiMkJSYnKCkiIiorLAAtLi8kITAxITIvMzQ1Njc4ADk6Ozw9Pj9ALkFCIkNERUYAR0hJSktMTU5PUFFSU1RVVgBXWFlaW1xdXl9gYWJjZGVmAGdoaWprbG1ub3BxcnN0dXYAd3h5ent8fX5/gIGCg4SFhgCHiImKgouMjY6PkJGSk5SVAJaXmJmaMZucnZ6fdaChoqMApKWmp6ipqqusra6vsLGyswC0tba3uLm6u7y9vr/AwcLDAMTFxsfIycrLzM3Oz9DR0tMA1NXW19jZ2tvc3d7f4OHi4wDk5ebn6Onq6+zt7u/w8fLzMc52JD1lDxwAAAAldEVYdGRhdGU6Y3JlYXRlADIwMjQtMDctMTBUMTU6MzA6MTArMDA6MDBIzYEAAAAAJXRFWHRkYXRlOm1vZGlmeQAyMDI0LTA3LTEwVDE1OjMwOjEwKzAwOjAwOZA5vAAAACh0RVh0ZGF0ZTp0aW1lc3RhbXAAMjAyNC0wNy0xMFQxNTozMDoxMSswMDowMMjyE9cAAAAASUVORK5CYII=
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
        self.stop_flag = threading.Event()
        self.auto_scroll_enabled = True
        self.websocket_task = None

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        if self.startup_checkbox_var.get():
            self.start_script()

    def load_config(self):
        if not os.path.exists(APPDATA_DIR):
            os.makedirs(APPDATA_DIR)
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
                self.vrchat_ip_entry.insert(0, config.get("vrchat_ip", "127.0.0.1"))
                self.vrchat_port_entry.insert(0, config.get("vrchat_port", "9000"))
                self.token_entry.insert(0, config.get("token", "YOUR_ACCESS_TOKEN_HERE"))
                self.startup_checkbox_var.set(config.get("start_on_startup", False))
        else:
            self.vrchat_ip_entry.insert(0, "127.0.0.1")
            self.vrchat_port_entry.insert(0, "9000")
            self.token_entry.insert(0, "YOUR_ACCESS_TOKEN_HERE")

    def save_config(self):
        config = {
            "vrchat_ip": self.vrchat_ip_entry.get(),
            "vrchat_port": self.vrchat_port_entry.get(),
            "token": self.token_entry.get(),
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
        token = self.token_entry.get()

        self.osc_client = udp_client.SimpleUDPClient(vrchat_ip, vrchat_port)
        self.console_text.insert(tk.END, f"Starting with VRChat IP: {vrchat_ip}, Port: {vrchat_port}, Token: {token}\n")
        self.auto_scroll()

        self.stop_flag.clear()
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.websocket_task = self.loop.create_task(self.run_websocket(token))
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
