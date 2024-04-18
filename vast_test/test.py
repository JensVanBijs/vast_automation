import clr
clr.AddReferenceToFileAndPath('C:/Program Files (x86)/Union Biometrica/VAST/USB2Comm.dll')
clr.AddReferenceToFileAndPath('C:/Program Files (x86)/Union Biometrica/VAST/VAST.exe')
from USB2Comm import UsbComm
from VAST import AccessConfig, LedCtrl
from System import UInt16

u = UsbComm()
acfg = AccessConfig(False)
usb = UsbComm(u.GetHexFile(
    clr.Convert(acfg.CypressPIDbeforeRenum, UInt16)), 
    clr.Convert(acfg.CypressPIDbeforeRenum, UInt16), 
    clr.Convert(acfg.CypressPIDafterRenum, UInt16)
    )
led = LedCtrl()
led.UsbCom = usb

print(led.LedState)

