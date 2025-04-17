
import clr
import System

class Usb2Comm():
    def __init__(self):
        clr.AddReference("C:/Program Files (x86)/Union Biometrica/VAST/USB2Comm.dll")
        from USB2Comm import UsbComm
        self.usb = UsbComm(UsbComm.GetHexFile(6553), 6553, 8198)
        
    # def SendAllMotionBuffer(self, command:str, value: System.Byte):
    #     if self.usb == None:
    #         raise Exception("USB communication not initialized.")
    #     try:
    #         self.usb.SendAllMotionBuffer(command, value)
    #     except Exception as e:
    #         print(f"Error sending command {command}: {e}")
            
    # def WriteSPI_Word(self, command: System.Byte, address: System.Byte, value: System.UInt16):
    #     if self.usb == None:
    #         raise Exception("USB communication not initialized.")
    #     try:
    #         self.usb.WriteSPI_Word(command, address, value)
    #     except Exception as e:
    #         print(f"Error writing SPI word: {e}")
       
    # def ReadbackSPI_Word(self, address: System.UInt16) -> System.UInt16:
    #     if self.usb == None:
    #         raise Exception("USB communication not initialized.")
    #     try:
    #         return self.usb.ReadbackSPI_Word(address)
    #     except Exception as e:
    #         print(f"Error reading SPI word: {e}")
    #         return None


