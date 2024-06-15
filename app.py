import datetime

import requests
from flask import Flask, request, jsonify, redirect, render_template, Response
from ultralytics import YOLO
import cv2
import math
import easyocr
import subprocess  # For running PHP scripts
import os  # For file path manipulation

# Initialize EasyOCR
reader = easyocr.Reader(['en'])

# Initialize Flask
app = Flask(__name__)

# Model
model = YOLO("yolov8-License_Plate.pt")

# Global variable to store detected text
detected_text = ""


# Function to process frames
def process_frame(frame):
    global detected_text
    results = model(frame, stream=True)

    # Coordinates
    for r in results:
        boxes = r.boxes

        for box in boxes:
            # Bounding box
            x1, y1, x2, y2 = box.xyxy[0]
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)  # Convert to int values

            # Put box in cam
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 255), 3)

            # Confidence
            confidence = math.ceil((box.conf[0] * 100)) / 100
            print("Confidence --->", confidence)

            # Extract region of interest (ROI)
            roi = frame[y1:y2, x1:x2]

            # Run OCR on ROI
            result = reader.readtext(roi)

            # Display recognized text above the box
            if len(result) > 0:
                recognized_text = result[0][1]
                detected_text = recognized_text  # Store detected text in global variable

                org = (x1, y1 - 10)
                font = cv2.FONT_HERSHEY_SIMPLEX
                fontScale = 1
                color = (255, 0, 0)
                thickness = 3
                cv2.putText(frame, recognized_text, org, font, fontScale, color, thickness)

    return frame


# Video streaming generator
def generate_frames():
    cap = cv2.VideoCapture(0)
    cap.set(3, 640)
    cap.set(4, 480)

    while True:
        success, frame = cap.read()

        if not success:
            break

        processed_frame = process_frame(frame)
        ret, buffer = cv2.imencode('.jpg', processed_frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')


@app.route('/')
def index():
    return render_template('index.html')  # Main page


@app.route('/video_feed')
def video_feed():
    # Return the video stream
    return Response(
        generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )


@app.route('/detected_text')
def get_detected_text():
    global detected_text
    return detected_text


@app.route('/check_car', methods=['POST'])
def check_car():
    car_number = request.form.get("car_number")  # Get data from AJAX request

    if not car_number:
        return "No car number provided", 400  # Return 400 Bad Request if input is invalid

    # Call the PHP script with the car number
    php_script_path = os.path.join(app.root_path, "templates", "check_car.php")  # Ensure this path is correct
    # Send HTTP POST request to the PHP script (assuming a local web server running PHP)
    php_script_url = "http://localhost/CarCheck/Car/check_car.php"  # Update with the correct URL

    # Make a POST request to the PHP script with the car_number
    response = requests.post(php_script_url, data={'car_number': car_number})

    if response.status_code == 200:
        output = response.text  # Clean the PHP script output
        return output  # Return the response to the client
    else:
        return "Error: Unable to check car", 500  # Handle errors


@app.route('/result', methods=['GET'])
def result():
    # Example plate number to query the PHP script
    plate_number = request.args.get("car_number")

    # URL of the PHP script that fetches car details
    php_script_url = "http://localhost/CarCheck/Car/get_car.php"

    # Send a POST request to the PHP script with the plate number
    response = requests.post(php_script_url, data={"plate_number": plate_number})

    if response.status_code == 200:
        car_details = response.json()  # Parse the JSON response
    else:
        car_details = None  # Handle the error case

    # Check if the license is still valid
    current_year = datetime.datetime.now()
    expiration_date = datetime.datetime.strptime(car_details.get("car_license_expiration_date"), "%Y-%m-%d")
    car_valid = expiration_date >= current_year
    return render_template("result.html", car=car_details, car_valid=car_valid)

if __name__ == "__main__":
    app.run(debug=True)
