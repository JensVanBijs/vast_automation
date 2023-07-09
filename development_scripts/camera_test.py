# %% Init
import pymmcore_plus
import matplotlib.pyplot as plt
import os
import numpy as np


# %% Create constants
mmc = pymmcore_plus.CMMCorePlus()

mm_dir = r"C:\Program Files\Micro-Manager-2.0"
data_dir = os.path.abspath("./../../../data/development_data")
config_file = r"leicaCTR6000.cfg"

mmc.setDeviceAdapterSearchPaths([mm_dir])
os.add_dll_directory(r"C:\Program Files\Micro-Manager-2.0")

print(mmc.getVersionInfo())
print(mmc.getAPIVersionInfo())


# %% Load config file
mmc.loadSystemConfiguration(os.path.join(mm_dir, config_file))
print(f"Loaded config file: {config_file} from path {os.path.join(mm_dir, config_file)}")
print(f"Loaded device labels are: {mmc.getLoadedDevices()}")


# %% Snap image (grayscale)
mmc.snapImage()
img = mmc.getImage()

plt.imshow(img, cmap="gray")


# %% Snap image (colour)
mmc.setProperty("BaumerOptronic", "PixelType", "32bitRGB")
mmc.snapImage()
img = mmc.getImage()

img = img.view(dtype=np.uint8).reshape(img.shape[0], img.shape[1], 4)[...,2::-1]
img = img[:,:,::-1]
plt.imshow(img)


# %% Save image
plt.imshow(img)
plt.savefig(os.path.join(data_dir, "test_picture.png"))

