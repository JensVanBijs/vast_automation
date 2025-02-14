# from controllers.LEICA_control import MicroscopeManager
# import numpy as np
# import useq
# import cv2
# import pymmcore_plus

# mm = MicroscopeManager()

# core = mm.core

# @core.mda.events.frameReady.connect
# def on_frame(image: np.ndarray, event: useq.MDAEvent):
#     # save image
#     cv2.imwrite("image.tiff", image)

# seq = [useq.MDAEvent(
#     properties=[useq.PropertyTuple("Transmitted Light", "State", 1),
#                 useq.PropertyTuple("Transmitted Light", "Level", 40)],
# )]

# mm._light = 1
# mm.switch_objective("4x")
# mm.switch_objective("2.5x")
# core.run_mda(seq)

# mmc = pymmcore_plus.CMMCorePlus()
# mmc.loadSystemConfiguration("C:/Program Files/Micro-Manager-2.0/CTR6000.cfg")
# mmc.waitForSystem()


import matplotlib.pyplot as plt
import os
import pymmcore_plus
import numpy as np

core = pymmcore_plus.CMMCorePlus()
core.enableDebugLog(True)

# Sidenote:
# I would have expected this line to have added the folder to your PATH
# so you shouldn't *have* to use add_dll_directory... but let me know if not
core.setDeviceAdapterSearchPaths([r"C:\Program Files\Micro-Manager-2.0"])
micromanager_directory = r"C:\Program Files\Micro-Manager-2.0"
os.add_dll_directory(micromanager_directory)

# Load devices -------------------------

core.loadDevice("COM1", "SerialManager", "COM1")
core.loadDevice("Scope", "LeicaDMI", "Scope")
core.loadDevice("Transmitted Light", "LeicaDMI", "Transmitted Light")
core.loadDevice('BaumerOptronic','BaumerOptronic','BaumerOptronic')

# pre-init props -----------------------
core.setProperty("Scope", "AnswerTimeOut", 250)
core.setProperty("Scope", "Port", "COM1")
# you might need more of those COM pre-init props here
core.setProperty("COM1", "BaudRate", 19200)
core.setProperty("COM1", "DTR", "Disable")
core.setProperty("COM1", "DataBits", 8)
core.setProperty("COM1", "Parity", "None")
core.setProperty("COM1", "StopBits", 1)
core.setProperty("COM1", "Handshaking", "Off")
core.setProperty("COM1", "Verbose", 1)
core.setProperty("COM1", "Fast USB to Serial", "Disable")

# parent labels -------------------------
core.setParentLabel("Transmitted Light", "Scope")

# Initialize devices -------------------
# equivalent of config: Property,Core,Initialize,1
core.initializeAllDevices()

# Roles -------------------------------
# equivalent of config: Property,Core,Camera,BaumerOptronic
core.setCameraDevice("BaumerOptronic")
# equivalent of config: Property,Core,AutoShutter,1
core.setAutoShutter(True)  # <--------

# turn on light
tl = pymmcore_plus.Device("Transmitted Light", core)
_light = tl.getPropertyObject("State")
_brightness = tl.getPropertyObject("Level")
_light = 1
_brightness = 40

img = core.snap()
# Sidenote: I would have expected snap() to reshape/fix the image for you... no?
print(img.dtype, img.shape, img.min(), img.max(), img.mean())

img = img.view(dtype=np.uint8).reshape(img.shape[0], img.shape[1], 4)[...,2::-1]
img = img[:,:,::-1]
plt.imshow(img)
plt.show()

core.reset()