# 2024 SUAV Electronics

This repository contains the onboard code for the SUAV drone, developed for the SUAS 2024 aerospace engineering competition. The software includes features such as autonomous flight operations, geotagged imaging, and payload mechanism control.

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Directory Structure](#directory-structure)
- [Author](#author)

## Overview
The software is designed to run on a Raspberry Pi integrated with the drone's flight controller. It also controls external electronic systems onboard, such as the imaging system and stepper motor payload winch system. The application is event-driven, with requests handled via Python Flask endpoints.

The drone communicates with the Ground Control Station (GCS) using a RocketM5 with 5.8G antennas linked to a router, over a localhost network. All flight operations are executed using MAVLink.

All code on the main branch of this repository has been verified using an aerial vehicle (AV). Do not push to main unless verified with an AV as this software is mission-critical and safety-critical. 

### For SUAV Members:
When making future edits, please avoid pushing directly to the master branch. Instead, follow these steps:
1. Create your own branch.
2. Complete your changes.
3. Create a pull request to merge back into the master branch.
4. Add `Lmah0` as a reviewer for the pull request.

## Features
- **Autonomous Flight Operations**: Includes takeoff, waypoint navigation, and landing.
- **Geotagged Imaging**: Captures and transmits geotagged images to the GCS.
- **Payload Control**: Manages the payload mechanism using stepper motors.
- **Real-time Data**: Pulls and returns real-time flight data from the flight controller.

## Directory Structure
- **SUAS2024.py**: Core application controlling the stepper motors, camera/imaging system, flight mode switching, and aerial vehicle operations.
- **arm.py**: Arms the drone, enabling rotor operation.
- **initialize.py**: Connects to the vehicle and verifies the heartbeat signal.
- **mode.py**: Switches flight modes (e.g., takeoff, landing, autonomous, manual).
- **takeoff.py**: Executes drone takeoff to a specified altitude.
- **camera.py**: Flask server for geotagged imaging, saving images locally.
- **pixhawk.py**: Custom MAVProxy module for real-time flight data retrieval.
- **stepperMotor.py**: Controls the stepper motor payload systems.
- **fastBootAll.bash**: Runs MAVProxy with `pixhawk.py` and starts `SUAS2024.py`.
- **fastBootMAVProxy.bash**: Boots up MAVProxy on the flight controller.
- **fastBootSUAS.bash**: Quickly starts `SUAS2024.py`.
- **killProcessOnPort.bash / killPython.bash**: Kills Python processes on the Raspberry Pi.

## Author
Written by Liam Mah, 2023-2024.
