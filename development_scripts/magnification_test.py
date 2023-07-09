# %% Init
# import pymmcore
import pymmcore_plus
import matplotlib.pyplot as plt
import os
import numpy as np
from time import sleep


# %% Create constants
# mmc = pymmcore.CMMCore()
mmc = pymmcore_plus.CMMCorePlus()

mm_dir = r"C:\Program Files\Micro-Manager-2.0"
config_file = r"CTR6000.cfg"

mmc.setDeviceAdapterSearchPaths([mm_dir])
os.add_dll_directory(r"C:\Program Files\Micro-Manager-2.0")

print(mmc.getVersionInfo())
print(mmc.getAPIVersionInfo())


# %% Load config file
mmc.loadSystemConfiguration(os.path.join(mm_dir, config_file))
print(f"Loaded config file: {config_file} from path {os.path.join(mm_dir, config_file)}")
print(f"Loaded device labels are: {mmc.getLoadedDevices()}")


# %% Move table down

# mmc.getXYPosition()
print(f"Start position Z: {mmc.getZPosition()} microm, in reality this is position -13.30 mm")
sleep(10)
mmc.setZPosition(0.0)
print(f"0.0 is {mmc.getZPosition()}")
sleep (10)

mmc.setPosition(-4940.00)
sleep(10)
print(f"Absolute low position Z: {mmc.getZPosition()} microm, in reality this is position -18.24 mm")


# %%

magnification = pymmcore_plus.Device("ObjectiveTurret", mmc)
magnification_state = magnification.getPropertyObject("State")

TEN = 0
EMPTY = 1
NOTHING = [3, 5, 6]
TWO_POINT_FIVE = 2
FOUR = 4

