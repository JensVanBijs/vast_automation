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


# %% Change lenses

lens = pymmcore_plus.Device("IL-Turret", mmc)
lens_state = lens.getPropertyObject("State")

# Set: Fluorescence - Green
lens_state.value = 0
sleep(3)

# Set: Bright field

lens_state.value = 1
sleep(3)
# lens_state.value = 2
# sleep(3)
# lens_state.value = 4
# sleep(3)

# Set: Fluorescence - Blue

lens_state.value = 3
