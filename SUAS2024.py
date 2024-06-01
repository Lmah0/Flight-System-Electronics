# Built to sync with GCS2024 in SUAV repo
# Built for raspberry pi OS (Linux)

# Built by Liam Mah (May 2024)

from picamera2 import Picamera2, Preview
from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import threading
import socket
import json
import sys
import time
# from io import BytesIO
from os import path
import argparse
import RPi.GPIO as GPIO

import Operations.arm as arm
import Operations.initialize as initialize
import Operations.mode as autopilot_mode
import Operations.takeoff as takeoff
import Operations.waypoint as waypoint


GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

UDP_PORT = 5005
DELAY = 1
CW = 1  # Clockwise stepper rotation
CCW = 0  # Counter-clockwise stepper rotation
DIR1 = 27  # Direction pin of motor 1
STEP1 = 17  # Step pin of motor 1
DIR2 = 24
STEP2 = 23
SPR = 200  # Steps per revolution
STEPPER_DELAY = 1 / 3500  # Generic delay (lower = faster spin)
mode = (14, 15, 18)
GPIO.setup(mode, GPIO.OUT)
resolution = {'Full': (0, 0, 0)}  # not the whole dict, just wrote fullstep for now

GPIO.output(mode, resolution['Full'])  # Picking full step
picam2 = None
vehicle_connection = None

# GPIO Motor Setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(DIR1, GPIO.OUT)  # Set DIR1 pin as output
GPIO.setup(STEP1, GPIO.OUT)  # Set STEP1 pin as output
GPIO.setup(DIR2, GPIO.OUT)    #Set DIR2 pin as output 
GPIO.setup(STEP2, GPIO.OUT)   #Set STEP2 pin as output
# ----

gcs_url = "http://192.168.1.65:80"  # Web process API url (RocketM5)
vehicle_port = "udp:127.0.0.1:5006"  # Make sure to run mavproxy script with 'mavproxy.py --out=udp:127.0.0.1:5006'

# Dictionary to maintain vehicle state
vehicle_data = {
    "last_time": 0,
    "lat": 0,
    "lon": 0,
    "rel_alt": 0,
    "alt": 0,
    "roll": 0,
    "pitch": 0,
    "yaw": 0,
    "dlat": 0,
    "dlon": 0,
    "dalt": 0,
    "heading": 0
}

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Overriding CORS for external access

@app.route('/stepperUpMotor1', methods=['POST'])  # Stepper motor reels up
def reel_up_motor1():
    data = request.json
    try:
        rotations = int(data['rotations'])
    except Exception as e:
        return {'message': 'Error. Invalid input.'}, 400  # 400 BadRequest

    GPIO.output(DIR1, CCW)  # Set direction to SPIN (CW OR CCW)
    for x in range(SPR * rotations):
        y = x / (SPR * rotations)  # Y is the percentage through the movement
        damping = 4 * (y - 0.5)**2 + 1  # smoothing formula
        # damping = 1
        GPIO.output(STEP1, GPIO.HIGH)  # MOVEMENT SCRIPT
        time.sleep(STEPPER_DELAY * damping)
        GPIO.output(STEP1, GPIO.LOW)
        time.sleep(STEPPER_DELAY * damping)
    return {'message': 'Success!'}, 200

@app.route('/stepperDownMotor1', methods=['POST'])  # Stepper motor drops payload
def reel_down_motor1():
    data = request.json
    try:
        rotations = int(data['rotations'])
    except Exception as e:
        return {'message': 'Error. Invalid input.'}, 400  # 400 BadRequest

    GPIO.output(DIR1, CW)  # Set direction to SPIN (CW OR CCW)
    for x in range(SPR * rotations):
        y = x / (SPR * rotations)  # Y is the percentage through the movement
        damping = 4 * (y - 0.5)**2 + 1  # smoothing formula
        # damping = 1
        GPIO.output(STEP1, GPIO.HIGH)  # MOVEMENT SCRIPT
        time.sleep(STEPPER_DELAY * damping)
        GPIO.output(STEP1, GPIO.LOW)
        time.sleep(STEPPER_DELAY * damping)
    return {'message': 'Success!'}, 200

@app.route('/stepperUpMotor2', methods=['POST'])  # Stepper motor reels up
def reel_up_motor2():
    data = request.json
    try:
        rotations = int(data['rotations'])
    except Exception as e:
        return {'message': 'Error. Invalid input.'}, 400  # 400 BadRequest

    GPIO.output(DIR2, CCW)  # Set direction to SPIN (CW OR CCW)
    for x in range(SPR * rotations):
        y = x / (SPR * rotations)  # Y is the percentage through the movement
        damping = 4 * (y - 0.5)**2 + 1  # smoothing formula
        # damping = 1
        GPIO.output(STEP2, GPIO.HIGH)  # MOVEMENT SCRIPT
        time.sleep(STEPPER_DELAY * damping)
        GPIO.output(STEP2, GPIO.LOW)
        time.sleep(STEPPER_DELAY * damping)
    return {'message': 'Success!'}, 200

@app.route('/stepperDownMotor2', methods=['POST'])  # Stepper motor drops payload
def reel_down_motor2():
    data = request.json
    try:
        rotations = int(data['rotations'])
    except Exception as e:
        return {'message': 'Error. Invalid input.'}, 400  # 400 BadRequest

    GPIO.output(DIR2, CW)  # Set direction to SPIN (CW OR CCW)
    for x in range(SPR * rotations):
        y = x / (SPR * rotations)  # Y is the percentage through the movement
        damping = 4 * (y - 0.5)**2 + 1  # smoothing formula
        # damping = 1
        GPIO.output(STEP2, GPIO.HIGH)  # MOVEMENT SCRIPT
        time.sleep(STEPPER_DELAY * damping)
        GPIO.output(STEP2, GPIO.LOW)
        time.sleep(STEPPER_DELAY * damping)
    return {'message': 'Success!'}, 200

@app.route('/cameraOn', methods=['POST'])  # Turns on camera, API body is number of pics requested
def trigger_camera():
    global picam2
    data = request.json
    try:
        amount_of_pictures_requested = int(data["amount_of_pictures"])
    except Exception as e:
        return {'message': 'Error. Invalid input.'}, 400  # 400 BadRequest

    if picam2 is None:
        picam2 = Picamera2()
        camera_config = picam2.create_still_configuration()
        picam2.configure(camera_config)
        picam2.start_preview(Preview.NULL)
        picam2.start()
        time.sleep(1)
    else:
        picam2.start()

    for i in range(amount_of_pictures_requested):
        start_time = time.time()
        current_time = take_and_send_picture(i, picam2)
        time_elapsed_since_start = current_time - start_time
        delay_time = DELAY - time_elapsed_since_start
        if delay_time > 0:
            time.sleep(delay_time)  # 1 picture per second
    picam2.stop()
    return {'message': 'Success!'}, 200

@app.route('/set_flight_mode', methods=['POST'])  # Sets the flight mode
def set_mode():
    # Ardupilot docs (for flight modes): https://ardupilot.org/copter/docs/parameters.html
    data = request.json
    try:
        mode_id = int(data['mode_id'])
        print(mode_id)
        print(autopilot_mode.set_mode(vehicle_connection, mode_id))
    except Exception as e:
        return jsonify({'error': "Invalid operation."}), 400

    return jsonify({'message': 'Mode set successfully'}), 200

@app.route('/coordinate_waypoint', methods=['POST'])  # Flies waypoint at 25m (82ft)
def fly_waypoint():
    data = request.json
    try:
        latitude = float(data['latitude'])
        longitude = float(data['longitude'])
        altitude = 25
    except Exception as e:
        return jsonify({'error': 'Invalid data'}), 400

    waypoint.absolute_movement(vehicle_connection, latitude, longitude, altitude)

    return jsonify({'message': 'Waypoint set successfully'}), 200

@app.route('/set_mode_and_waypoint', methods=['POST'])  # Sets guided mode and flies waypoint at 25m (82ft)
def set_mode_and_waypoint():
    data = request.json
    try:
        latitude = float(data['latitude'])
        longitude = float(data['longitude'])
        altitude = 25
    except Exception as e:
        return jsonify({'error': 'Invalid data'}), 400

    guided_mode = 4
    autopilot_mode.set_mode(vehicle_connection, guided_mode)
    time.sleep(1)
    waypoint.absolute_movement(vehicle_connection, latitude, longitude, altitude)

    return jsonify({'message': 'Guided mode and waypoint set successfully'}), 200

def take_and_send_picture(i, picam2):
    print('capturing image %i' % i)
    filepath = '/home/pi/Desktop/SUAV/picam/images/' + f'capture{i}.jpg'
    jsonpath = filepath.rsplit('.', 1)[0] + '.json'
    image = picam2.capture_image('main')

    image.save(filepath, None)

    with open(jsonpath, 'w') as json_file:
        json.dump(vehicle_data, json_file)

    # Send image to GCS
    payload = {}
    files = [
        ('file', (path.basename(filepath), open(filepath, 'rb'), 'image/jpeg'))
    ]
    headers = {}
    response = requests.request("POST", f"{gcs_url}/submit", headers=headers, data=payload, files=files)

    payload = {}
    files = [
        ('file', (path.basename(jsonpath), open(jsonpath, 'rb'), 'application/json'))
    ]
    headers = {}
    response = requests.request("POST", f"{gcs_url}/submit", headers=headers, data=payload, files=files)

    return time.time()

# def take_and_send_picture_no_local(i, picam2):
#     print('capturing image %i' % i)
    
#     # Capture image into a BytesIO object
#     image_stream = BytesIO()
#     image = picam2.capture_image('main')
#     image.save(image_stream, format='JPEG')
#     image_stream.seek(0)

#     # Serialize vehicle data into a JSON string
#     vehicle_data_json = json.dumps(vehicle_data)

#     # Send image to GCS
#     files = {
#         'file': ('capture.jpg', image_stream, 'image/jpeg'),
#     }
#     headers = {}
#     response = requests.request("POST", f"{gcs_url}/submit", headers=headers, files=files)

#     # Send JSON to GCS
#     json_stream = BytesIO(vehicle_data_json.encode('utf-8'))
#     json_files = {
#         'file': ('data.json', json_stream, 'application/json'),
#     }
#     response = requests.request("POST", f"{gcs_url}/submit", headers=headers, files=json_files)

#     return time.time()

def receive_vehicle_position():  # Actively runs and receives live vehicle data on a separate thread
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    sock.bind(("127.0.0.1", UDP_PORT))
    while True:
        data = sock.recvfrom(1024)
        items = data[0].decode()[1:-1].split(",")
        message_time = float(items[0])

        if message_time <= vehicle_data["last_time"]:
            continue

        vehicle_data["last_time"] = message_time
        vehicle_data["lon"] = float(items[1])
        vehicle_data["lat"] = float(items[2])
        vehicle_data["rel_alt"] = float(items[3])
        vehicle_data["alt"] = float(items[4])
        vehicle_data["roll"] = float(items[5])
        vehicle_data["pitch"] = float(items[6])
        vehicle_data["yaw"] = float(items[7])
        vehicle_data["dlat"] = float(items[8])
        vehicle_data["dlon"] = float(items[9])
        vehicle_data["dalt"] = float(items[10])
        vehicle_data["heading"] = float(items[11])

if __name__ == "__main__":
    position_thread = threading.Thread(target=receive_vehicle_position, daemon=True)
    position_thread.start()
    time.sleep(1)

    print(f"Attempting to connect to port: {vehicle_port}")
    vehicle_connection = initialize.connect_to_vehicle(vehicle_port)
    print("Vehicle connection established.")
    retVal = initialize.verify_connection(vehicle_connection)
    print("Vehicle connection verified.")

    if not retVal:
        print("Error. Could not connect and/or verify a valid connection to the vehicle.")
        sys.exit(1)

    app.run(debug=True, host='0.0.0.0')
