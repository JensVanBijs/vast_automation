import clr
import System

class LedSettings():
    def __init__(self):
        self._limitCurr = System.Array.CreateInstance(System.Double, 5)
        self._curr = System.Array.CreateInstance(System.Double, 5)

        for i in range(5):
            self._limitCurr[i] = 1.0
            self._curr[i] = 1.0
        
        self._limitCurr[0] = 1
        self._limitCurr[1] = 1

class LedCtrl():
    def __init__(self, usbComm):
        self._ledBits = System.Array.CreateInstance(System.UInt32, 5)
        self._dacGainCfg = 32768
        self._dacLdacCfg = 40960
        self._dacChanEn = 49407
        self._usbComm = usbComm
        self._ledState = 49407
        self._spiAdr = 2

    def InitDac(self, ledSettings: LedSettings):
        if self._usbComm == None:
            return
        
        self._ledBits[0] = 1
        self._ledBits[1] = 2
        self._ledBits[2] = 4
        self._ledBits[3] = 8
        self._ledBits[4] = 16
        self._usbComm.WriteSPI_Word(System.Byte(0), System.Byte(2), self._dacGainCfg)
        self._usbComm.WriteSPI_Word(System.Byte(0), System.Byte(2), self._dacLdacCfg)
        self._usbComm.WriteSPI_Word(System.Byte(0), System.Byte(2), self._dacChanEn)
        self.SetLed(49406, ledSettings, False)

    def SetLed(self, state: int, ledSettings: LedSettings, setCurr: bool):
        self._ledState = state
        if self._usbComm == None:
            return
        
        self._usbComm.WriteSPI_Word(System.Byte(0), System.Byte(2), self._ledState)
        if not setCurr:
            return
        self.SetCurrent(1, ledSettings._curr[0])
        self.SetCurrent(2, ledSettings._curr[1])
    
    def SetCurrent(self, ch: int, curr: System.Double):
        num = int((ch - 1 & 7) << 12)
        wData = int(4095.0 * (curr / 2.0) + num)
        if self._usbComm == None:
            return

        self._usbComm.WriteSPI_Word(System.Byte(0), System.Byte(2), wData)

    def LedOnOff(self, ch: int, onOff: bool, delay: int):
        ledBit = self._ledBits[ch - 1]
        if onOff:
            self._ledState &= ~ledBit
        else:
            self._ledState |= ledBit

        if self._usbComm == None:
            return

        self._usbComm.WriteSPI_Word(System.Byte(0), System.Byte(2), System.UInt16(self._ledState))
        System.Threading.Thread.Sleep(delay)
        print(f"Led {ch} {'ON' if onOff else 'OFF'}")