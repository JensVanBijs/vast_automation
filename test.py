from controllers.Usb2Comm import Usb2Comm
from controllers.LED_Control import LedCtrl, LedSettings
from enum import Enum
import clr
import System
import time

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
        self._usbComm = usb
        self._initialised = False
        self._pumpAddr = 1
        self._pumpBusy = False
        self._error = 0
        self._lastDirP = False
        self._waitingForResponse = False
        self._terminated = False
        self.Baudrates = Enum("Baudrates", "e9p6KBAUD e19p2KBAUD e38p4KBAUD e57p6KBAUD")