# %% Init

import mouse
import keyboard
from time import sleep

mouse.move(833, 10)
mouse.click("left")

def take_vast_picture(name):
    mouse.move(21, 32)
    mouse.click("left")
    mouse.move(76, 148)
    mouse.click("left")
    mouse.move(155, 430)
    mouse.click("left")

    sleep(1)
    keyboard.write(f"VAST_{name}")

    sleep(0.3)

    mouse.move(464, 506)
    mouse.click("left")

def rotate_vast():
    mouse.move(400, 925)
    mouse.click("left")
    sleep(0.5)


