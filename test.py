from controllers.Usb2Comm import Usb2Comm
from controllers.LED_Control import LedCtrl, LedSettings
import time

def Test_LED_Control():
    usb = Usb2Comm().usb # Get USB driver for sending commands
    ledSettings = LedSettings() # init Led settings object
    ledControl = LedCtrl(usb) # init Led control object
    ledControl.InitDac(ledSettings=ledSettings) # run init for Leds

    time.sleep(1) 
    for i in range(5):
        ledControl.LedOnOff(i+1, False, 1) # turn all LEDs off

    time.sleep(1) 

    ledControl.LedOnOff(1, True, 1) # change current of LED 1
    time.sleep(1)
    ledControl.SetCurrent(1, 0.75)
    time.sleep(1)
    ledControl.SetCurrent(1, 0.5)
    time.sleep(1)
    ledControl.SetCurrent(1, 0.25)
    time.sleep(1)
    ledControl.SetCurrent(1, 1)
    time.sleep(1)

    ledControl.LedOnOff(1, False, 1)


if __name__ == "__main__":
    Test_LED_Control() 