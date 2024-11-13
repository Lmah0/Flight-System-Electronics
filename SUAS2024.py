# Built to sync with GCS2024 in SUAV repo
# Built for raspberry pi OS (Linux)

# Built by Liam Mah (May 2024)

from picamera2 import Picamera2, Preview
from flask import Flask, jsonify, request
from flask_cors import CORS
from math import ceil
import requests
import threading
import socket
import json
import sys
import time
from io import BytesIO
from os import path
import argparse
import RPi.GPIO as GPIO

import Operations.arm as arm
import Operations.initialize as initialize
import Operations.mode as autopilot_mode
import Operations.takeoff as takeoff
import Operations.waypoint as waypoint

gcs_url = "http://192.168.1.65:80"  # Web process API url (RocketM5)
vehicle_port = "udp:127.0.0.1:5006"  # Make sure to run mavproxy script with 'mavproxy.py --out=udp:127.0.0.1:5006'

ALTITUDE = 25

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

UDP_PORT = 5005

DIAM = 0.03 # Diameter of spool in meters 
DELAY = 1
DIR1 = 27  # Direction pin of motor 1
STEP1 = 17  # Step pin of motor 1
DIR2 = 24
STEP2 = 23
SPR = 200  # Steps per revolution
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
GPIO.setup(DIR2, GPIO.OUT)    # Set DIR2 pin as output 
GPIO.setup(STEP2, GPIO.OUT)   # Set STEP2 pin as output
# ----

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

stepper_directions_1 = {
    "UP": 0,
    "DOWN": 1
}

stepper_directions_2 = {
    "UP": 0,
    "DOWN": 1
}

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Overriding CORS for external access

@app.route('/stepper_motor_1', methods=['POST'])  # Stepper motor 1 control
def stepper_motor_1():
    data = request.json
    try:
        distance = float(data['distance'])
        direction = str(data['direction'])
        speed = int(data['speed'])

    except Exception as e:
        return {'message': 'Error. Invalid input.'}, 400
    
    lower_limit = 1000
    upper_limit = 4000

    if speed < lower_limit or speed > upper_limit:
        return {'message': 'Error. Invalid speed. Speed above upper limit or below lower limit.'}, 400
    
    if speed <= 0:
        return {'message': 'Error. Invalid speed. Speed must be greater than 0.'}, 400
    
    bitwise_direction = stepper_directions_1[direction]

    stepper_delay = 1 / speed  # Generic delay (lower = faster spin)

    GPIO.output(DIR1, bitwise_direction)  # Set direction to SPIN (CW OR CCW)
    distance = distance / (DIAM * 3.1415926)  
    for x in range(ceil(SPR * distance)):
        y = x / (SPR * distance)  # Y is the percentage through the movement
        damping = 4 * (y - 0.5)**2 + 1  # smoothing formula
        GPIO.output(STEP1, GPIO.HIGH)  # MOVEMENT SCRIPT
        time.sleep(stepper_delay * damping)
        GPIO.output(STEP1, GPIO.LOW)
        time.sleep(stepper_delay * damping)
    return {'message': 'Success!'}, 200

@app.route('/stepper_motor_2', methods=['POST'])  # Stepper motor 2 control
def stepper_motor_2():
    data = request.json
    try:
        distance = float(data['distance'])
        direction = str(data['direction'])
        speed = int(data['speed'])
    except Exception as e:
        return {'message': 'Error. Invalid input.'}, 400

    lower_limit = 1000
    upper_limit = 4000

    if speed < lower_limit or speed > upper_limit:
        return {'message': 'Error. Invalid speed. Speed above upper limit or below lower limit.'}, 400

    if speed <= 0:
        return {'message': 'Error. Invalid speed. Speed must be greater than 0.'}, 400

    bitwise_direction = stepper_directions_2[direction]

    stepper_delay = 1 / speed  # Generic delay (lower = faster spin)

    GPIO.output(DIR2, bitwise_direction)
    distance = distance / (DIAM * 3.1415926)
    for x in range(ceil(SPR * distance)):
        y = x / (SPR * distance)  # Y is the percentage through the movement
        damping = 4 * (y - 0.5)**2 + 1  # smoothing formula
        GPIO.output(STEP2, GPIO.HIGH)  # MOVEMENT SCRIPT
        time.sleep(stepper_delay * damping)
        GPIO.output(STEP2, GPIO.LOW)
        time.sleep(stepper_delay * damping)
    return {'message': 'Success!'}, 200

@app.route('/camera_on', methods=['POST'])  # Turns on camera, API body is number of pics requested
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
        current_time = take_and_send_picture_no_local(i, picam2)
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

@app.route('/takeoff', methods=['POST'])
def takeoff_vehicle():
    data = request.json
    try:
        altitude = float(data['altitude'])
        takeoff.takeoff(vehicle_connection, altitude)
    except Exception as e:
        return jsonify({'error': 'Invalid data'}), 400

    return jsonify({'message': 'Takeoff successful'}), 200

@app.route('/coordinate_waypoint', methods=['POST'])  # Flies waypoint at 25m (82ft)
def fly_waypoint():
    data = request.json
    print(f"Waypoint request JSON paylod: {data}")
    try:
        latitude = float(data['latitude'])
        longitude = float(data['longitude'])
        altitude = float(data['altitude'])
        print("Parsed latitude: {latitude}, longitude {longitude}")
    except Exception as e:
        return jsonify({'error': f'Invalid data. Error {e}'}), 400

    try:
        waypoint.absolute_movement(vehicle_connection, latitude, longitude, altitude)
        return jsonify({'message': 'Waypoint set successfully'}), 200
    except Exception as e:
        return jsonify({'error': f'Failed to set waypoint. Error: {e}'}), 400

def take_and_send_picture(i, picam2):
    '''
    Takes a picture and sends it back to the GCS. It saves the images locally on the Raspberry Pi, and can cause the SD card on
    the Raspberry Pi to fill and corrupt. Be careful when using this.
    '''
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

def take_and_send_picture_no_local(i, picam2):
    '''
    Takes a picture and sends it back to the GCS. It does not save any images locally on the Raspberry Pi, and is used to prevent
    the SD card on the Raspberry Pi from filling and overloading the storage (and corrupting data).
    '''
    print('capturing image %i' % i)
    
    # Capture image into a BytesIO object
    image_stream = BytesIO()
    image = picam2.capture_image('main')
    image.save(image_stream, format='JPEG')
    image_stream.seek(0)

    # Serialize vehicle data into a JSON string
    vehicle_data_json = json.dumps(vehicle_data)

    # Send image to GCS
    files = {
        'file': (f'capture{i}.jpg', image_stream, 'image/jpeg'),
    }
    headers = {}
    response = requests.request("POST", f"{gcs_url}/submit", headers=headers, files=files)

    # Send JSON to GCS
    json_stream = BytesIO(vehicle_data_json.encode('utf-8'))
    json_files = {
        'file': (f'capture{i}.json', json_stream, 'application/json'),
    }
    response = requests.request("POST", f"{gcs_url}/submit", headers=headers, files=json_files)

    return time.time()

@app.route('/locator', methods=['GET'])
def picture_locator():
    global picam2

    if picam2 is None:
        picam2 = Picamera2()
        camera_config = picam2.create_still_configuration()
        picam2.configure(camera_config)
        picam2.start_preview(Preview.NULL)
        picam2.start()
        time.sleep(1)
    else:
        picam2.start()

    try:
        image_stream = BytesIO()
        image = picam2.capture_image('main')
        image.save(image_stream, format='JPEG')
        image_stream.seek(0)

        image_file = {
            'file': (f'locator.jpg', image_stream, 'image/jpeg'),
        }

        headers = {}
        response = requests.request("POST", f"{gcs_url}/submit", headers=headers, files=image_file)
    except Exception as e:
        return {'message': 'Error. Could not capture and send image.'}, 400
    picam2.stop()
    return {'message': 'Success!'}, 200

def receive_vehicle_position():  # Actively runs and receives live vehicle data on a separate thread
    '''
    This function is ran on a second thread to actively retrieve and update the vehicle state. This vehicle state contains GPS and vehicle orientation.
    These are pulled at the time of taking an image in order to geotag images and support target localization.
    '''
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
