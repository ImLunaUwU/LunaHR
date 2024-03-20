import tkinter as tk
import threading
import signal
from pythonosc import dispatcher, osc_server

class OscReceiverApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("OSC Receiver")
        self.root.geometry("300x150")  # Set the window dimensions (width x height)

        self.label_ones_hr = tk.Label(self.root, text="Ones HR: ")
        self.label_ones_hr.pack()

        self.label_tens_hr = tk.Label(self.root, text="Tens HR: ")
        self.label_tens_hr.pack()

        self.label_hundreds_hr = tk.Label(self.root, text="Hundreds HR: ")
        self.label_hundreds_hr.pack()

        self.label_heart_rate = tk.Label(self.root, text="Heart Rate: ")
        self.label_heart_rate.pack()

        # Define a dispatcher for handling OSC messages
        self.dispatcher = dispatcher.Dispatcher()
        self.dispatcher.map("/vrchat/heart_rate/ones_hr", self.update_ones_hr)
        self.dispatcher.map("/vrchat/heart_rate/tens_hr", self.update_tens_hr)
        self.dispatcher.map("/vrchat/heart_rate/hundreds_hr", self.update_hundreds_hr)
        self.dispatcher.map("/vrchat/heart_rate/heart_rate", self.update_heart_rate)

        self.server = osc_server.ThreadingOSCUDPServer(('127.0.0.1', 9000), self.dispatcher)
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True  # Set the thread as daemon to close when the main thread exits

        # Set up a signal handler to properly close the server on termination
        signal.signal(signal.SIGINT, self.handle_signal)

    def start_osc_server(self):
        self.server_thread.start()

    def handle_signal(self, event=None, signum=None, frame=None):
        print("Closing OSC server...")
        self.server.shutdown()
        self.server.server_close()
        self.server_thread.join()
        print("OSC server closed")
        self.root.destroy()


    def update_ones_hr(self, unused_addr, ones_hr):
        self.root.after(0, lambda: self.label_ones_hr.config(text=f"Ones HR: {ones_hr}"))

    def update_tens_hr(self, unused_addr, tens_hr):
        self.root.after(0, lambda: self.label_tens_hr.config(text=f"Tens HR: {tens_hr}"))

    def update_hundreds_hr(self, unused_addr, hundreds_hr):
        self.root.after(0, lambda: self.label_hundreds_hr.config(text=f"Hundreds HR: {hundreds_hr}"))

    def update_heart_rate(self, unused_addr, heart_rate):
        self.root.after(0, lambda: self.label_heart_rate.config(text=f"Heart Rate: {heart_rate}"))

    def start(self):
        self.start_osc_server()
        self.root.protocol("WM_DELETE_WINDOW", self.handle_signal)  # Bind the close button to the signal handler
        self.root.mainloop()

app = OscReceiverApp()
app.start()
