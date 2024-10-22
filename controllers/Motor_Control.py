from .Usb2Comm import Usb2Comm
import System

class Motor():
    def __init__(self, usbComm: Usb2Comm, motIdx: int = 1):
        self.accelScalar = 10
        self.zAxisRes = 20100
        self.zMotVelScaler = 1000
        self.maxZTravel = 110
        self.usbComm = usbComm
        self.addr = 1
        self._motorInd = motIdx
        self._accel = 5
        self._pwrPct = 50
        self._speed = 500000
        self.reverseDir = False

    def IniMotor(self, start: bool):
        if start and self.reverseDir:
            self.usbComm.SendAllMotionBuffer("F1", System.Byte(48 + self._motorInd))

        self.SendCmd(f'm{self._pwrPct}')

    def SendCmd(self, cmd: str):
        if self.usbComm == None:
            return
        self.usbComm.SendAllMotionBuffer(cmd, System.Byte(bytes(f'{self.addr}'.encode('utf-8'))[0]))
    
    def RotateToPos(self, degree: float, acc: int, vel: int, backlash: int):
        if self.usbComm == None:
            return

        num1 = int(abs(degree) / 50.0 * 36.0)
        num2 = backlash / 50.0 * 36.0
        if degree != 0.0 and num1 == 0:
            num1 = 1
        
        if num1 <= 0:
            print("RotateToPos does nothing")
            return
        
        scmd = f"aM1V{vel}"
        if degree > 0.0:
            scmd += f"P{num1}"
        else:
            num3 = num1 + num2
            scmd += f"D{num3}"
            if num2 > 0.0:
                scmd += f"P{num2}"
        
        self.SendCmd(scmd)
    
    def ResetPos(self):
        num = 120000.0
        self.usbComm.WriteSPI_Word(System.Byte(128), System.Byte(24), System.UInt16(0))
        data = (self.usbComm.ReadbackSPI_Word(System.UInt16(0)) & 1)
        cmd = f"aM{self._motorInd}V200P0" if (int(data) & 1) <= 0 else f"aM{self._motorInd}V200D0"
        self.SendCmd(cmd)