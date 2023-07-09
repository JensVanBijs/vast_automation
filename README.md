# VAST automation

> This github repository contains code created by _Siebe van Benthum_ and _Jens van Bijsterveld_ while working on their bachelor thesis for the Leiden Institute of Advance Computer Science (_LIACS_).
>
> Usage of the code is outlined in this readme file

As outlined in the paper written for the bachelor thesis [TODO](https://github.com), this code is split into multiple parts.

The first layer of abstraction contains the libraries for controlling the Leica microscope and the VAST system. The second layer contains two different ways to use these libraries for image capture. The third layer of abstraction contains code for a UI that facilitates easy use of one of the two implementations from the second layer.

## Microscope control

Microscope control is defined in `controllers/LEICA_control.py`.

This code uses the [microManager](https://micro-manager.org/) implementation [pymmcore_plus](https://github.com/pymmcore-plus/pymmcore-plus) to control the LEICA microscope used in this project.

The subdirectory `controllers/microscope_settings` contains two files that specify settings for the LEICA microscope. `CTR6000.cfg` is the microManager configuration file used for initialising the microManager core. `microscope_configuration.json` contains specific handles for certain occulars and lenses with some measurements that are used to facilitate certain operations.

## VAST control

VAST control is defined in `controllers/VAST_control.py`.

TODO

## Implementations

`ui_spoofing_implementation.py`

`external_imaging_implementation.py`

## User interface

`external_imaging_ui.py`
