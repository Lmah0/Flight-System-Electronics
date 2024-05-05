# Built to sync with GCS2024 in SUAV repo
# Built for raspberry pi OS (Linux)

from picamera2 import Picamera2, Preview
import sys
import time
import requests
from exif import Image
import piexif
from flask import Flask
import threading
import requests
import socket
import types
import json
from os import path

UDP_PORT = 5005
IMAGE_PATH = "./images/"
DELAY = 2

camera_state = 0  # 0: off, 1: on
picture_id = 0
picam2 = None
lock = threading.Lock()  # Thread locking for synchronizing shared resources
gcs_url = "http://192.168.1.76:80"

state = types.SimpleNamespace()
state.last_time = 0
state.lat = 0
state.lon = 0
state.rel_alt = 0
state.alt = 0
state.roll = 0
state.pitch = 0
state.yaw = 0
state.dlat = 0
state.dlon = 0
state.dalt = 0
state.heading = 0
state.image_number = 0

app = Flask(__name__)

@app.route('/cameraOff', methods=['POST'])
def stop_camera():
    global camera_state
    with lock:
        camera_state = 0

@app.route('/cameraOn', methods=['POST'])
def trigger_camera():
    global camera_state, picam2
    with lock:
        picam2 = Picamera2()
        camera_config = picam2.create_still_configuration()
        picam2.configure(camera_config)
        picam2.start_preview(Preview.NULL)
        picam2.start()
        time.sleep(1)
        camera_state = 1

    while camera_state == 1:
        start_time = time.time()
        current_time = take_and_send_picture()
        time.sleep(DELAY - (start_time - current_time))  # 1 picture per second

def take_and_send_picture():
    global picture_id, picam2
    with lock:
        img_name = f"capture{picture_id}"
        filepath = f"{IMAGE_PATH}capture{picture_id:04}.jpg"
        jsonpath = f"{IMAGE_PATH}capture{picture_id:04}.json"

        image = picam2.capture_image("main")
        image.save(filepath, None)

        receive_vehicle_position(jsonpath)

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

        picture_id += 1

        return time.time()

def receive_vehicle_position(json_path):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("127.0.0.1", UDP_PORT))
    
    data = sock.recvfrom(1024)
    items = data[0].decode()[1:-1].split(",")
    message_time = float(items[0])
    
    if message_time <= state.last_time:
        return
    
    state.last_time = message_time
    state.lat = float(items[1])
    state.lon = float(items[2])
    state.rel_alt = float(items[3])
    state.alt = float(items[4])
    state.roll = float(items[5])
    state.pitch = float(items[6])
    state.yaw = float(items[7])
    state.dlat = float(items[8])
    state.dlon = float(items[9])
    state.dalt = float(items[10])
    state.heading = float(items[11])

    # Create a dictionary with the data
    data_dict = {
        "last_time": state.last_time,
        "lat": state.lat,
        "lon": state.lon,
        "rel_alt": state.rel_alt,
        "alt": state.alt,
        "roll": state.roll,
        "pitch": state.pitch,
        "yaw": state.yaw,
        "dlat": state.dlat,
        "dlon": state.dlon,
        "dalt": state.dalt,
        "heading": state.heading
    }

    # Write the data to the JSON file
    with open(json_path, "w") as json_file:
        json.dump(data_dict, json_file, indent=4)

if __name__ == "__main__":
    if len(sys.argv) == 2:
        gcs_url = sys.argv[1]

    app.run(debug=True, host='0.0.0.0', threaded=True)