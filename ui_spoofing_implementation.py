# %% Imports and constants
from mm_code.mm_wrapper import MicroscopeManager
from time import sleep, time
import os
import mouse
import keyboard

# %% Define functions
def focus_vast_ui() -> None:
    """Change the window focus from the current window to the VAST UI"""
    mouse.move(833, 10)
    mouse.click("left")


def set_degrees(degrees: float) -> None:
    """Set the amount of degrees the VAST turns with a single click"""
    degrees = str(degrees).replace(".", ",")
    mouse.move(432, 924)
    mouse.click("left")
    mouse.click("left")
    keyboard.write(degrees)


def move_vast(direction: str, distance: int) -> None:
    times = distance // 1000
    remainder = distance - distance * times
    
    if direction == 'left':
        coor = (145, 927)
    elif direction == 'right':
        coor = (183, 927)

    for t in range(times):
        mouse.move(219, 930)
        mouse.click("left")
        mouse.click("left")
        keyboard.write(str(1000))
        sleep(0.1)
        mouse.move(*coor)
        mouse.click("left")
        sleep(2)
    if remainder:
        mouse.move(219, 930)
        mouse.click("left")
        mouse.click("left")
        keyboard.write(str(remainder))
        sleep(0.1)
        mouse.move(*coor)
        mouse.click("left")
        

def toggle_traylight() -> None:
    mouse.move(20, 963)
    mouse.click("left")


def vast_picture(image_label: str) -> None:
    """Takes a picture using the VAST camera"""
    # Move to file tab
    mouse.move(21, 32)
    mouse.click("left")

    # Move to save image menu entry
    mouse.move(76, 148)
    mouse.click("left")

    # Move to document name bar
    mouse.move(155, 430)
    mouse.click("left")

    # Write image name
    sleep(0.5)
    keyboard.write(f"VAST_{image_label}")

    # Save image
    mouse.move(464, 506)
    mouse.click("left")


def rotate_vast() -> None:
    """Clicks the rotate button in the VAST UI"""
    mouse.move(400, 925)
    mouse.click("left")


def define_sharpness(leica: MicroscopeManager) -> float:
    """Asks the user to define the height at which the zebrafish is sharp"""
    input("Please place the microscope at a height where the zebrafish clearly visible with this occular. \
          Press enter when done.")
    height = leica.core.getZPosition()
    return height

def define_distance() -> int:
    """Asks the user to measure the distance between the tail end and the head of the zebrafish being visible by moving it for this objective."""
    input("Please move the VAST system until the end part of the tail is visible.")
    input("Please measure how much micrometers of VAST movement is necassary to move to a frame where the end part of the head is visible.")
    size = input("Please enter your measurement in micrometers")
    input("Please place the zebrafish at its leftmost position.")
    return int(size)

def user_input(leica, occulars):
    user_info = dict()
    if "2.5x" in occulars:
        leica.switch_objective("2.5x")
        user_info["2.5x"] = (define_sharpness(leica), -1)
    if "4.0x" in occulars:
        leica.switch_objective("4x")
        user_info["4.0x"] = (define_sharpness(leica), define_distance())
    if "10.0x" in occulars:
        leica.switch_objective("10x")
        user_info["10.0x"] = (define_sharpness(leica), define_distance())
    return user_info

def check_start() -> None:
    """Asks the user to check if all UI elements are in the correct start positions."""
    input("Please check if the VAST camera target directory is empty.")
    input("Please check if the traylight is turned on.")

# %% Define main function

def microscope_loop(leica:MicroscopeManager, times, height, i=0):
    for idx in range(1, times+1):
                leica.full_imaging(label=f"{i}_{idx}", height=height)
                sleep(0.5)
                rotate_vast()

def main(testing = False, occulars = []):
    # Initialise microscope
    leica = MicroscopeManager()
    leica.switch_filter("White")
    leica.wait()

    check_start()

    info = user_input(leica, occulars)
    input("Please put the zebrafish in the middle position.")
    input("Please ensure the microscope is in camera mode.")

    # Focus on the VAST User Interface
    focus_vast_ui()

    if not testing:
        # move_vast("left", 8*500)
        degrees = 3.6
        times = 100
    elif testing:
        degrees = 60.0
        times = 6
    # Initialise VAST interface values
    set_degrees(degrees)

    # VAST pictures
    for idx in range(1, times+1):
        vast_picture(idx)
        sleep(0.5)
        rotate_vast()

    toggle_traylight()

    # 2.5x pictures
    if "2.5x" in occulars:
        leica.switch_objective("2.5x")
        focus_vast_ui()
        microscope_loop(leica, times, height=info["2.5x"][0])

    # 4.0x pictures
    if "4.0x" in occulars:
        leica.switch_objective("4x")
        focus_vast_ui()
        for i in range(2):
            microscope_loop(leica, times, height=info["4.0x"][0], i=i)
            move_vast("right", info["4.0x"][1]//2)
        move_vast("left", info["4.0x"][1])

    # 10.0x pictures
    if "10.0x" in occulars:
        leica.switch_objective("10x")
        focus_vast_ui()
        for i in range(4):
            microscope_loop(leica, times, height=info["10.0x"][0], i=i)
            move_vast("right", info["4.0x"][1]//4)
        move_vast("left", info["4.0x"][1])

    toggle_traylight()


# %% Execute main function (but not if the file is imported)
if __name__ == "__main__":
    TEST =False
    OCCULARS = ["2.5x"]
    start = time()
    main(TEST, OCCULARS)
    runtime = time() - start
    print("The VAST is done after:", runtime)

# TODO: Code cleanup