# 2024 SUAV Electonics


Implemented to permit camera triggers onboard the drone. Will take and return images as well as image data (drone latitude, longitude, pitch, roll, yaw, etc.)<br>

SUAS2024.py - Command server for imaging and stepper motors<br>
camera.py - Command server for only imaging<br>
pixhawk.py - MAVProxy module downloaded onto the flight controller to query vehicle heartbeat and return realtime vehicle positioning data<br>
stepperMotor.py - Code to trigger and test stepper motor functionality
