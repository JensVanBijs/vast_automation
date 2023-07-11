# VAST automation

> This github repository contains code created by _Siebe van Benthum_ and _Jens van Bijsterveld_ while working on their bachelor thesis for the Leiden Institute of Advance Computer Science (_LIACS_). The project was supervised by _professor Fons Verbeek_.

As outlined in the paper written for the bachelor thesis [TODO](https://github.com), this code is split into multiple parts.

The first layer of abstraction contains the libraries for controlling the Leica microscope and the VAST system. The second layer contains two different ways to use these libraries for image capture. The third layer of abstraction contains code for a UI that facilitates easy use of one of the two implementations from the second layer.

The `development_scripts` directory contains scripts that were used to test and debug specific parts of the controllers (layer one). These can be used to assert control works as expected.

## Microscope control

Microscope control is defined in `controllers/LEICA_control.py`.

This code uses the [microManager](https://micro-manager.org/) implementation [pymmcore_plus](https://github.com/pymmcore-plus/pymmcore-plus) to control the LEICA microscope used in this project.

The subdirectory `controllers/microscope_settings` contains two files that specify settings for the LEICA microscope. `CTR6000.cfg` is the microManager configuration file used for initialising the microManager core. `microscope_configuration.json` contains specific handles for certain occulars and lenses with some measurements that are used to facilitate certain operations.

## VAST control

VAST control is defined in `controllers/VAST_control.py`.

VAST control is achieved through usage of an Arduino UNO created by _Maarten Lamers_. This device, called the greybox, uses the VAST BioImagers TTL triggers in order to communicate with the device. The VAST control library facilitates serial communication between the greybox and the computer through usage of the [pyserial](https://github.com/pyserial/pyserial) library.

## Implementations

Using the control libraries, two implementations were made.

### UI spoofing

The UI spoofing implementation (`ui_spoofing_implementation.py`) contains code for controlling the VAST system through simulating user interaction using the [mouse](https://github.com/boppreh/mouse) and [keyboard](https://github.com/boppreh/keyboard) libraries.

This implementation works, but has some drawbacks. This means the external imaging implementation is prefered.

### External imaging

The external imaging implementation (`external_imaging_implementation.py`) uses the VAST systems TTL ports for communication. It uses the fact that actions can be defined per pair of recieved/sent TTL triggers in the VAST application and the arduino greybox to automate VAST actions while acquiring images with the microscope camera.

## User interface

A temporary user interface was made for the external imaging implementation. This user interface can be found in the `external_imaging_ui.py` file.

The user interface does not adhere to any of the rules for UI design, but allows for users to run the external imaging application without any experience with python code.

# TODO

- Refactor paths in paper
- Create paper reference
- Change paper reference to repository
- Create pseudocode for UI structure and paper
- Explain order of operations for external imaging
- Update default heights for main external imaging implementation

# Future work

- Update zebrafish distances for occulars
- VAST camera scripting through external imaging
- Add imaging options for each objective instead of for all objectives simultaneously (UI)
