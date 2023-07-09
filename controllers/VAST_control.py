#%%

import serial
from serial.tools.list_ports import comports
from time import sleep

class VastManager:

    def __init__(self) -> None:
        # header = b"\xff"
        self.serial_obj = self.connect_with_arduino()

        self.wait()
        response = self.serial_obj.read_all()
        if response != b"OK\n":
            raise ConnectionError("Connection with arduino failed")
        self.serial_obj.flush()

    @staticmethod
    def connect_with_arduino():
        for port, description, hwid in comports():
            if "Arduino Uno" in description:
                print(port, description, hwid)
                return serial.Serial(port, baudrate=115200)

    def wait(self):
        while not self.serial_obj.in_waiting:
            sleep(0.1)
        
    def listen_for_response(self):
        self.wait()
        response = self.serial_obj.read_all()
        if response == b'R1\n':
            return 1  # Pulse from VAST port IN.1
        elif response == b'R2\n':
            return 2  # Pulse from VAST port IN.2
        elif response == b'E0\n' or response == b'E1\n' or response == b'E2\n' or response == b'E3\n':
            print(response)
            return 3  # Error message
        elif response == b'OK\n':
            return 4  # All is well on the western front
        else:
            print(response)
            return 5  # Either unknown or print action
        
    def get_settings(self):
        self.serial_obj.write(b"X?\n")
        self.wait()
        response = self.serial_obj.read_all()
        response = [r.strip() for r in response.decode().split("\n")]

        info = dict()        
        if response[0] != "OK":
            return ConnectionError("X? command returned an unknown code.")
        else:
            for i, c in zip(range(4), ["KV", "XH", "XP", "XD", "XB"]):
                info[c] = response[i+1][3:]
        return info
    
    def trigger_vast(self):
        self.serial_obj.write(b"TT\n")
        self.wait()
        if self.listen_for_response() == 4:
            return True
        else:
            return False
        
    def sort_vast(self):
        self.serial_obj.write(b"TS\n")
        self.wait()
        if self.listen_for_response() == 4:
            return True
        else:
            return False


# %%
