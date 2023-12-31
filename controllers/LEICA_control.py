import pymmcore_plus
import matplotlib.pyplot as plt
import os
import numpy as np
import json
from PIL import Image
from time import sleep


class MicroscopeManager:

    def __init__(self) -> None:
        self.core = pymmcore_plus.CMMCorePlus()
        micromanager_directory = r"C:\Program Files\Micro-Manager-2.0"
        config_file = r"CTR6000.cfg"

        # self.core.setDeviceAdapterSearchPaths([os.path.join(os.path.pardir(os.path.abspath(__file__)), "microscope_settings")])
        self.core.setDeviceAdapterSearchPaths([micromanager_directory])
        os.add_dll_directory(micromanager_directory)
        self.core.loadSystemConfiguration(os.path.join(micromanager_directory, config_file))

        self.device_tags = [x for x in self.core.getLoadedDevices()]

        if not self.device_tags:
            return MicroscopeManagerError("No device tags were found.")
        elif not "IL-Turret" in self.device_tags:
            return MicroscopeManagerError("IL-Turret (lenses) not in device tags.")
        elif not "Transmitted Light" in self.device_tags:
            return MicroscopeManagerError("Transmitted Light not in device tags.")
        elif not "ObjectiveTurret" in self.device_tags:
            return MicroscopeManagerError("ObjectiveTurret not in device tags.")
        
        lens_device = pymmcore_plus.Device("IL-Turret", self.core)
        self._lens = lens_device.getPropertyObject("State")

        light_device = pymmcore_plus.Device("Transmitted Light", self.core)
        self._brightness = light_device.getPropertyObject("Level")
        self._light = light_device.getPropertyObject("State")

        objectives = pymmcore_plus.Device("ObjectiveTurret", self.core)
        self._objectives = objectives.getPropertyObject("State")

        self.core.setProperty("BaumerOptronic", "PixelType", "32bitRGB")
        plt.axis('off')

        self.image = np.array([])
        self.z = self.core.getZPosition()
        self.core.setZPosition(0.0)
        self.wait()

        dirpath = os.path.dirname(os.path.abspath(__file__))
        with open(f"{dirpath}/microscope_settings/microscope_configuration.json") as f:
            self.config = json.load(f)

    def __str__(self) -> str:
        return f"A class that manages the interaction between micromanager \
            and the Leica microscope.\nIt has the following device tags: \
            {self.device_tags}"
    
    def wait(self):
        while True:
            if not self.core.systemBusy():
                return

    @property
    def lens(self):
        return self._lens.value
    
    @lens.setter
    def lens(self, value):
        GREEN = 0
        BRIGHT_FIELD = 1
        BLUE = 3
        if value != GREEN and value != BRIGHT_FIELD and value != BLUE:
            return MicroscopeManagerError("Given lens value is not a supported lens (should be 0 (green), 1 (bright field), or 3 (blue)).")
        else:
            self._lens.value = value

    @property
    def light(self):
        return self._light.value
    
    @light.setter
    def light(self, value):
        if value not in [0, 1]:
            return MicroscopeManagerError("Light can only be on (1) or off (0).")
        else:
            self._light.value = value

    @property
    def brightness(self):
        return self._brightness.value
    
    @brightness.setter
    def brightness(self, value):
        if value not in range(0, 255):
            return MicroscopeManagerError("Brightness ranges from 0 to 255.")
        else:
            self._brightness.value = value

    @property
    def objective(self):
        return self._objectives.value
    
    @objective.setter
    def objective(self, value):
        EMPTY = 1
        NOTHING = [3, 5, 6]
        TWO_POINT_FIVE = 2
        TEN = 0
        FOUR = 4
        if value != TWO_POINT_FIVE and value != TEN and value != FOUR:
            return MicroscopeManagerError("Unknown objective.")
        else:
            self.core.setZPosition(-4940.00)
            self.wait()
            self._objectives.value = value
            self.wait()
            self.core.setZPosition(self.z)

    
    def snap_picture(self):
        img = self.core.snap()
        img = img.view(dtype=np.uint8).reshape(img.shape[0], img.shape[1], 4)[...,2::-1]
        img = img[:,:,::-1]
        self.image = img
        return img

    def show_picture(self):
        plt.imshow(self.image)

    def save_picture(self, picture, filename):
        dirpath = os.path.dirname(os.path.abspath(__file__)) 
        data_dir = os.path.abspath(f"{dirpath}/../data")
        plt.imshow(picture)
        img = Image.fromarray(picture)
        img.save(os.path.join(data_dir, filename))

    def switch_objective(self, name):
        objectives = self.config['objectives']
        if name not in objectives:
            raise ValueError(f"{name} is not a valid objective name.")
        objective = objectives[name]

        self.objective = objective['turret_location']
        self.core.setZPosition(objective['bf_zheight'])
        self.brightness = objective['brightness']

    def switch_filter(self, name):
        filters = self.config["filters"]
        if name not in filters:
            raise MicroscopeManagerError(f"{name} is not a valid filter name.")
        filter = filters[name]

        self.lens = filter["filter_location"]
        if filter["fluorescence"] == 0:
            self.wait()
            self.light = 1

    def full_imaging(self, label, height, filters):
        objectives = {
            0: "10x",
            2: "2.5x",
            4: "4x",
        }
        objective = objectives[self.objective]
        imaging_options = self.config["filters"]
        self.core.setZPosition(height)
        self.wait()
        for filter, settings in imaging_options.items():
            if filter in filters:
                self.lens = settings["filter_location"]
                self.core.setExposure(settings["exposure"])
                self.wait()
                if settings["fluorescence"] == 0:
                    self.light = 1
                    self.brightness = self.config["objectives"][objective]["brightness"]
                    sleep(2)
                img = self.snap_picture()
                self.save_picture(img, f"{objective}_{filter}_{label}.png")
            else:
                continue
            

class MicroscopeManagerError(Exception):

    def __init__(self, message):
        super().__init__(message)
        self.message = message
