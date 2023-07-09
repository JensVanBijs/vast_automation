#%%

import serial
from serial.tools.list_ports import comports
from time import sleep

def wait(serial_object):
    while not serial_object.in_waiting:
        sleep(0.1)

def connect_with_arduino():
    for port, description, hwid in comports():
        if "Arduino Uno" in description:
            print(port, description, hwid)
            return serial.Serial(port, baudrate=115200)
        
def listen_for_response(serial_object):
    wait(serial_object)
    response = serial_object.read_all()
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


arduino = connect_with_arduino()
header = b"\xff"

arduino.flush()
wait(arduino)
response = arduino.read_all()

if response != b"OK\n":
    raise ConnectionError("Connection with arduino failed")

# %%
arduino.write(b"X?\n")
wait(arduino)

returned = arduino.read_all()
print(returned)

# %%

