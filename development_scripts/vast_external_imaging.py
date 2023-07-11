# %% Init
import os

data_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.abspath(f"{data_dir}/../../../data")

with open(os.path.abspath(f"{data_dir}/external.txt"), "w") as file_obj:
    for i in range(1, 101):
        tomography = " no"
        x_position = 0
        degrees = round((i * 3.6)%360, 2)
        ctrl_output = 1
        trigger_input = 1
        adjust_rotation = "no"
        tray_LED = "off"
        
        row = f"{tomography}\t{str(x_position)}\t{str(degrees).replace('.', ',') + '0'}\t{ctrl_output}\t{trigger_input}\t{adjust_rotation}\t{tray_LED}\n"
        file_obj.write(row)

# %%
