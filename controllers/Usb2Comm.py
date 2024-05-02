import clr
import System

class Usb2Comm():
    def __init__(self):
        clr.AddReference("C:/Program Files (x86)/Union Biometrica/VAST/USB2Comm.dll")
        from USB2Comm import UsbComm
        self.usb = UsbComm(UsbComm.GetHexFile(6553), 6553, 8198)