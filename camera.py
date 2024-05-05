from picamera2 import Picamera2, Preview
import sys
import time
import requests
from exif import Image
import piexif
from flask import Flask
import threading
import requests

# Built to sync with GCS2024 in SUAV repo

app = Flask(__name__)

cameraState = 0  # 0: off, 1: on
pictureId = 0
picam2 = None
lock = threading.Lock() # Thread locking for synchronizing shares resources
gcsUrl = None

@app.route('/cameraOn', methods=['POST'])
def triggerCamera():
    global cameraState, picam2
    with lock:
        picam2 = Picamera2()
        camera_config = picam2.create_still_configuration()
        picam2.configure(camera_config)
        picam2.start_preview(Preview.NULL)
        picam2.start()
        time.sleep(1)
        cameraState = 1

    while cameraState == 1:
        takeAndSendPicture()

@app.route('/cameraOff', methods=['POST'])
def stopCamera():
    global cameraState
    with lock:
        cameraState = 0

def takeAndSendPicture():
    global pictureId, picam2
    with lock:
        directory = "/Users/liammah/Desktop/University/Schulich UAV/Electronics"
        filename = f"capture{pictureId}.jpg"
        pictureId += 1
        filepath = f"{directory}/{filename}"
        image = picam2.capture_image("main")
        image.save(filepath, None)
        

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 camera.py <GCS_URL>")
        sys.exit(1)
    
    gcsUrl = sys.argv[1]
    app.run(debug=True, host='0.0.0.0', threaded=True)

