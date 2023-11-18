testing = True

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
master.geometry("900x1000")

metadata_frame = tk.Frame(master, width=300, height=100, highlightbackground="black", highlightthickness=2)
metadata_frame.grid(row=0, column=1, pady=5)

prepare_frame = tk.Frame(master, width=300, height=100, highlightbackground="black", highlightthickness=2)
metadata_frame.grid(row=1, column=1, pady=5)

objective_frame = tk.Frame(master, width=300, height=100, highlightbackground="black", highlightthickness=2)
objective_frame.grid(row=2, column=0, pady=5)

channel_frame = tk.Frame(master, width=300, height=100, highlightbackground="black", highlightthickness=2)
channel_frame.grid(row=2, column=2, pady=5)

calibration_frame = tk.Frame(master, width=300, height=100, highlightbackground="black", highlightthickness=2)
calibration_frame.grid(row=3, column=1, pady=5)

imaging_frame = tk.Frame(master, width=300, height=100, highlightbackground="black", highlightthickness=2)
imaging_frame.grid(row=4, column=1, pady=5)

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


tk.Label(objective_frame, text="Objectives").pack(fill=None, expand=False)
for obj in objectives:
    exec(f"var_{obj} = tk.IntVar()")
    exec(f"but_{obj} = tk.Checkbutton(objective_frame, text='{obj}', variable=var_{obj}, onvalue=1, offvalue=0, command=click)")
    exec(f"but_{obj}.pack(side=tk.TOP, fill=None, expand=False)")

tk.Label(channel_frame, text="Fluorescence").pack(fill=None, expand=False)
for fluo in fluorescence:
    exec(f"var_{fluo} = tk.IntVar()")
    exec(f"but_{fluo} = tk.Checkbutton(channel_frame, text='{fluo}', variable=var_{fluo}, onvalue=1, offvalue=0, command=click)")
    exec(f"but_{fluo}.pack(side=tk.TOP, fill=None, expand=False)")


def execute():
    """Start executing the VAST loop through external imaging"""
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
    
calibrate = tk.Button(calibration_frame, text="Calibrate sharpness", command=define_sharpness)
calibrate.pack(fill=None, expand=False)

empty = tk.Button(prepare_frame, text="Image empty capilary", command=image_empty_capilary)
empty.pack(fill=None, expand=False)

create = tk.Button(calibration_frame, text="Create external imaging file", command=create_file)
create.pack(fill=None, expand=False)

test = tk.Button(imaging_frame, text="Take a testpicture", command=test_picture)
test.pack(fill=None, expand=False)

execute = tk.Button(imaging_frame, text="Start the imaging procedure", command=execute)
execute.pack(fill=None, expand=False)

tk.Label(metadata_frame, text="Experiment name").pack()
name = tk.Entry(metadata_frame, width=20)
name.pack(fill=None, expand=False)

tk.Label(metadata_frame, text="Amount of fishes that are to imaged").pack()
fishes = tk.Entry(metadata_frame, width = 20)
fishes.pack(fill=None, expand=False)


tk.mainloop()
