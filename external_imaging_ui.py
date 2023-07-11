testing = False

import tkinter as tk
from external_imaging_implementation import main, create_vast_rows, create_vast_file, calc_positions
from controllers.LEICA_control import MicroscopeManager
from controllers.VAST_control import VastManager
from tkinter import messagebox
import os

data_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.abspath(f"{data_dir}/data")

if not testing:
    leica = MicroscopeManager()
    assert leica
    vast = VastManager()
    assert vast.serial_obj.is_open

master = tk.Tk()
master.title("VAST automation control")
master.geometry("1080x920")

key = {
    "GreenFluorescence": "Blue",
    "RedFluorescence": "Green",
    "BrightField": "White",
    "TwoPointFive": "2.5x",
    "Four": "4x",
    "Ten": "10x",
}

selected = dict()
heights = dict()


objectives = ["TwoPointFive", "Four", "Ten"]
fluorescence = ["BrightField", "GreenFluorescence", "RedFluorescence"]

def click():
    for obj in objectives:
        exec(f"selected['{key[obj]}'] = var_{obj}.get()")
    for fluo in fluorescence:
        exec(f"selected['{key[fluo]}'] = var_{fluo}.get()")


tk.Label(master, text="Objectives").pack()
for obj in objectives:
    exec(f"var_{obj} = tk.IntVar()")
    exec(f"but_{obj} = tk.Checkbutton(master, text='{obj}', variable=var_{obj}, onvalue=1, offvalue=0, command=click)")
    exec(f"but_{obj}.pack(side=tk.TOP)")

tk.Label(master, text="Fluorescence").pack()
for fluo in fluorescence:
    exec(f"var_{fluo} = tk.IntVar()")
    exec(f"but_{fluo} = tk.Checkbutton(master, text='{fluo}', variable=var_{fluo}, onvalue=1, offvalue=0, command=click)")
    exec(f"but_{fluo}.pack(side=tk.TOP)")


def execute():
    """Start executing the VAST loop through external imaging"""
    # TODO: Vast camera scripting
    fish_amount = int(fishes.get())
    experiment_name = str(name.get())
    main(leica, vast, selected, heights, fish_amount, experiment_name)

def create_file():
    """Create the external imaging file based on the selected componenets"""
    objectives = [x for x in selected.keys() if x.endswith("x") and selected[x] == 1]
    file = list()
    for occular in objectives:
        positions = calc_positions(occular)
        for x in positions:
            file = [*file, *create_vast_rows(x_position=x)]
    create_vast_file(file)
    messagebox.showinfo(title="External imaging file created", message=f"The external imaging file has been created at location {data_dir} as external.txt")
    messagebox.showinfo(title="VAST application action", message="Please load external.txt into the VAST application under Imaging/Imaging with external device.")
    messagebox.showinfo(title="VAST application action", message="Please click the box: Enable external imaging and then click the button Run external imaging")

def image_empty_capilary():
    """Starts the capilary imaging procedure"""
    messagebox.showinfo(title="VAST application action", message="Please image the empty capilary using the VAST application. Press enter to continue.")
    messagebox.showinfo(title="VAST application action", message="Please turn of the VAST traylight. The leica camera will now image the empty capilary.")
    leica.switch_filter("White")
    leica.switch_objective("2.5x")
    leica.full_imaging("Empty_capilary_Leica", 16441.78396484375, ["White"])

def define_sharpness():
    """Starts the user sharpness definitions for all selected objectives"""
    objectives = [x for x in selected.keys() if x.endswith("x") and selected[x] == 1]
    for obj in objectives:
        leica.switch_objective(obj)
        messagebox.showinfo(title="Microscope action", message="Please place the microscope at a height where the zebrafish clearly visible with this occular.")
        height = leica.core.getZPosition()
        heights[obj] = height
    messagebox.showinfo(title="Assertion", message="Is the microscope placed in camera mode?")
    

def test_picture():
    """Snaps and saves a picture as test.png"""
    img = leica.snap_picture()
    leica.save_picture(img, "test.png")
    
calibrate = tk.Button(master, text="Calibrate sharpness", command=define_sharpness)
calibrate.pack()

empty = tk.Button(master, text="Image empty capilary", command=image_empty_capilary)
empty.pack()

create = tk.Button(master, text="Create external imaging file", command=create_file)
create.pack()

execute = tk.Button(master, text="Start the imaging procedure", command=execute)
execute.pack()

test = tk.Button(master, text="Take a testpicture", command=test_picture)
test.pack()

tk.Label(master, text="Amount of fishes that are to imaged").pack()
fishes = tk.Entry(master, width = 20)
fishes.pack()

tk.Label(master, text="Experiment name").pack()
name = tk.Entry(master, width=20)
name.pack()

tk.mainloop()

# TODO: imaging options for each objective
# TODO: Order of operation should be explained in the UI
# TODO: UI structure should be better (not just a long list) --> Subwindows
# BUG: Upgrade UI structure. Use pseudocode for this. Also put the pseudocode in the paper!
