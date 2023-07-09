#%% Imports and constants

from arduino_code.serial_wrapper import VastManager
from mm_code.mm_wrapper import MicroscopeManager
from time import sleep
import os
from ui_implementation import define_sharpness
import pandas as pd


data_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.abspath(f"{data_dir}/../../data")

# %% Helper functions

def create_vast_rows(x_position = 0, tomography = "no", ctrl_output = 1, trigger_input = 1, adjust_rotation = "no", tray_LED = "off"):
    rows = list()
    for i in range(1, 101):
        degrees = round((i * 3.6)%360, 2)
        row = f"{tomography}\t{str(x_position)}\t{str(degrees).replace('.', ',') + '0'}\t{ctrl_output}\t{trigger_input}\t{adjust_rotation}\t{tray_LED}\n"
        rows.append(row)

    return rows

def create_vast_file(rows: list) -> None:
    with open(os.path.abspath(f"{data_dir}/external.txt"), "w") as file_obj:
        for row in rows:
            file_obj.write(row)

def calc_positions(occular):
    if occular == "2.5x":
        return[0]
    elif occular == "4x":
        return [0, 1000, 2000]
    elif occular == "10x":
        return [0, 425, 850, 1275, 1700, 2125, 2550, 3000]
    
def init_metadata():
    return {
        "Experiment name": list(),
        "Fish number": list(),
        "Image capture number": list(),
        "Objective": list(),
        "X position": list(),
        "Filters": list()
    }
    
def add_metadata(metadata:dict, entry:dict):
    for k, e in entry.items():
        metadata[k].append(e)
    return metadata
    
def save_metadata(metadata:dict):
    df = pd.DataFrame.from_dict(metadata)
    df.to_json(f"{data_dir}/metadata.json")

def main(leica, vast, startup_info:dict = {"2.5x": 1, "4x": 0, "10x": 0, "White": 1, "Blue": 1, "Green": 0}, heights:dict = {"2.5x": 12, "4x": 12, "10x": 12}, fish_amount=1, experiment_name = "test"):  # TODO: heights should at least make some sense

    selected = [x for x in startup_info.keys() if startup_info[x] == 1]
    objectives = [x for x in selected if x.endswith("x")]
    filters = [x for x in selected if x not in objectives]

    metadata = init_metadata()
    for fish in range(fish_amount):
        for obj in objectives:
            leica.switch_objective(obj)
            for pos in calc_positions(obj):
                for idx in range(100):
                    while True:
                        try:
                            assert 1 == vast.listen_for_response()
                            break
                        except:
                            continue
                    leica.full_imaging(label=idx+1, height=heights[obj], filters=filters)
                    metadata_row = {
                        "Experiment name": experiment_name,
                        "Fish number": fish,
                        "Image capture number": idx,
                        "Objective": obj,
                        "X position": pos,
                        "Filters": filters
                    }
                    metadata = add_metadata(metadata, metadata_row)
                    sleep(1)
                    vast.trigger_vast()

    save_metadata(metadata)
    vast.trigger_vast()

# TODO: Rename file

