from controllers.Usb2Comm import Usb2Comm
from controllers.LED_Control import LedCtrl, LedSettings
from controllers.Motor_Control import Motor
from enum import Enum
import clr
import System
import time
import threading

def Test_LED_Control(led: int = 1):
    usb = Usb2Comm().usb # Get USB driver for sending commands
    ledSettings = LedSettings() # init Led settings object
    ledControl = LedCtrl(usb) # init Led control object
    ledControl.InitDac(ledSettings=ledSettings) # run init for Leds

    time.sleep(1) 
    for i in range(5):
        ledControl.LedOnOff(i+1, False, 1) # turn all LEDs off

    time.sleep(1) 

    ledControl.LedOnOff(led, True, 1) # change current of LED 1
    time.sleep(1)
    ledControl.SetCurrent(led, 0.75)
    time.sleep(1)
    ledControl.SetCurrent(led, 0.5)
    time.sleep(1)
    ledControl.SetCurrent(led, 0.25)
    time.sleep(1)
    ledControl.SetCurrent(led, 1)
    time.sleep(1)

    ledControl.LedOnOff(led, False, 1)

usb = Usb2Comm().usb

class PumpCtrl():
    def __init__(self, usbComm: Usb2Comm):
        self.testMode = False
        self._usbComm = usbComm
        self._initialised = False
        self._pumpAddr = 1
        self._pumpBusy = False
        self._error = 0
        self._lastDirP = False
        self._waitingForResponse = False
        self._verbose = False
        self._terminated = False
        self._timePrevCmd = time.time()
        self.Baudrates = Enum("Baudrates", "e9p6KBAUD e19p2KBAUD e38p4KBAUD e57p6KBAUD")

    def SendPumpCmd(self, cmd: str) -> bool:
        if self._waitingForResponse:
            return False
        
        self._pumpBusy = True
        if len(cmd) < 3:
            return False
        
        try:
            length = len(cmd)
            buf = System.Array.CreateInstance(System.Byte, length+1)
            for i in range(length):
                buf[i] = System.Byte(bytes(cmd[i].encode('utf-8')))
            buf[length] = System.Byte(13)
            charCount = System.Byte(System.UInt32(length) + System.UInt32(1))
            larmUsrt = self._usbComm.LARM_USRT
            larmCommux = self._usbComm.LARM_COMMUX
            numSecs = time.time() - self._timePrevCmd
            if numSecs < 30:
                time.sleep(30-numSecs)
                numSecs = 30

            self._usbComm.SendCommBuffer(buf, larmUsrt, larmCommux, System.UInt32(self.Baudrates), 0, charCount)
            if self._verbose or not cmd.endswith('Q'):
                print(f"VAST: {numSecs} Send pump command {cmd}")
            self._timePrevCmd = time.time()
            
        except Exception as e:
            print(f"An error occurred: {str(e)}")
        
        return True
    
    def InitPump(self, pos: int):
        num = 0
        self.SendPumpCmd(f'/{self._pumpAddr}YR')
        time.sleep(200/1000)

    def WaitPumpFinish(self, timeoutMs: int) -> bool:
        flag = False
        now = time.localtime()
        stat = System.Byte(0)
        while not flag and (time.localtime().tm_sec - now.tm_sec).real * 1000 < timeoutMs:
            flag, stat = self.IsPumpReady(stat)
            if not flag:
                time.sleep(200/1000)


        return flag

    def IsPumpReady(self, stat: System.Byte) -> tuple[bool, System.Byte]:
        if not self._pumpBusy or self.testMode or self._usbComm == None:
            return True, stat
        
        self.SendPumpCmd(f"/{self._pumpAddr}Q")
        self._waitingForResponse = True
        time.sleep(30/1000)
        num = 0
        buf = System.Array.CreateInstance(System.Byte, 64)
        for i in range(64):
            buf[i] = System.Byte(0)
        idx1 = 9
        elapsedMs = (time.time() - self._timePrevCmd)/1000
        if elapsedMs < 30:
            time.sleep(30/1000 - elapsedMs)

        flag = False
        if self._usbComm.CommReadBack(System.Byte(self._usbComm.LARM_USRT), buf):
            self._timePrevCmd = time.time()
            if buf[idx1] != 0:
                flag = int(buf[idx1]) & 32 > 1
                num = int(buf[idx1]) & 15
            else:
                flag = False

            stat = buf[idx1]
            if self._verbose:
                print(f"VAST: Pump {self._pumpAddr} status {stat}")

        else:
            flag = False

        self._waitingForResponse = False
        if self._terminated:
            print("VAST: Pump control terminated")
            self.Stop()
        
        if num > 0:
            print(f"VAST: Pump {self._pumpAddr} error {num}")

        return flag, stat
    
    def Stop(self):
        self._terminated = True
        if not self.SendPumpCmd(f"/{self._pumpAddr}T"):
            return
        self._terminated = False
        self._pumpBusy = False


from msl.loadlib import Server32, Client64, load_library

# class PvAPI32(Server32):
#     def __init__(self, host, port, **kwargs):
#         super(PvAPI32, self).__init__("./Drivers/PvAPI.dll", "cdll", host, port)
#         self.version = self.lib.PvVersion()

# class PvAPI(Client64):
#     def __init__(self):
#         super(PvAPI, self).__init__(module32="PvAPI32")

#     def __getattr__(self, name):
#         def send(*args, **kwargs):
#             return self.request(name, *args, **kwargs)
#         return send

PvAPI = load_library.LoadLibrary("C:/Program Files/Allied Vision Technologies/GigESDK/bin-pc/x64/PvAPI.dll", 'cdll')
PvNET = load_library.LoadLibrary("C:/Program Files/Allied Vision Technologies/GigESDK/bin-pc/x64/PvNET.dll", 'clr')
CameraCtrl = load_library.LoadLibrary("C:/Program Files (x86)/Union Biometrica.win7 08-12-22/VAST/CameraCtrl.dll", 'clr')
ProcessImage = load_library.LoadLibrary("C:/Program Files (x86)/Union Biometrica.win7 08-12-22/VAST/ProcessImage.dll", 'clr')
# clr.AddReference("C:/Program Files (x86)/Union Biometrica.win7 08-12-22/VAST/PvNET.dll")
# clr.AddReference("C:/Program Files (x86)/Union Biometrica.win7 08-12-22/VAST/CameraCtrl.dll")
# clr.AddReference("C:/Program Files (x86)/Union Biometrica.win7 08-12-22/VAST/ProcessImage.dll")

CameraSttgs = CameraCtrl.lib.CameraCtrl.CameraSettings()

