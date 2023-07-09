#%% Setup: Imports and backend
import usb.core as core
from usb.backend import libusb1
usb_backend = libusb1.get_backend()


#%% Print device information

#name of device is ReNumerated CyUsb3 .NET UBI
# NOTE: Product ID seems to change every time the device is reset. Currently: idProduct=0xB301
device = core.find(idVendor=0x0BD2)
print(len([x for x in device]))


#%% Create device configuration

assert device is not None, "No device found."
# assert LENGTH OF FOUND DEVICES = 1

configuration = device.configurations()[0]

interfaces = configuration.interfaces()

for i in range(len(interfaces)):
    print(f"Interface {i}")
    print(interfaces[i].endpoints())
    print()

# %%
interface = interfaces[0]

out_endpoints = [interface.endpoints()[0], interface.endpoints()[4]]
output = out_endpoints[0]

# if device.is_kernel_driver_active(interface):
#     device.detatch_kernel_driver(interface)

device.write(output.bEndpointAddress, [0x00, 0x00, 0x00, 0x02, 0xFF, 0xC0], interface.bInterfaceNumber)