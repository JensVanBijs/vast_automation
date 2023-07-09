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


# %%

for j in mmc.getLoadedDevices():
    tmp_device = pymmcore_plus.Device(j, mmc)
    print(j)
    # for x in range(len(tmp_device.properties)):
    #     print(tmp_device.properties[x])
    # print()
# %%

# Get camera settings
tmp_device = pymmcore_plus.Device("BaumerOptronic", mmc)
print()
for x in range(len(tmp_device.properties)):
    print(tmp_device.properties[x])
print()

#%%
tmp_device.properties[5].value

# %%
# mmc.setExposure
mmc.state()