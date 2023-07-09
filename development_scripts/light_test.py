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


# %% Turn light on

transmitted_light = pymmcore_plus.Device("Transmitted Light", mmc)
light_level = transmitted_light.getPropertyObject("Level")
light_on_off = transmitted_light.getPropertyObject("State")

# Turn light on
light_on_off.value = 1

# Set brightness (scales form 0 to 255)

print("Off")
light_level.value = 0

sleep(5)

print("On")
light_level.value =  255

sleep(5)

light_level = 20
light_on_off = 0
