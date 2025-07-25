from flask import Flask, render_template, request, jsonify
from inference_sdk import InferenceHTTPClient
import base64, tempfile, os, serial, time

app = Flask(__name__)

# Initialize Roboflow client
CLIENT = InferenceHTTPClient(
    api_url="https://serverless.roboflow.com",
    api_key="bwkyjP9TSy6zV6vVksD8"  # replace with your actual Roboflow API key
)
MODEL_ID = "agriweedsdetection_1/8"

# Initialize Arduino serial
arduino = serial.Serial('COM5', 9600)  # Replace 'COM5' with your Arduino port
time.sleep(2)  # Allow Arduino time to reset

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/detect', methods=['POST'])
def detect():
    data = request.json['image']
    image_data = base64.b64decode(data.split(',')[1])

    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
        temp_file.write(image_data)
        temp_file_path = temp_file.name

    try:
        # Inference using Roboflow model
        result = CLIENT.infer(temp_file_path, model_id=MODEL_ID)
        os.remove(temp_file_path)

        # Debug output for predictions
        print("Roboflow Result:", result)

        weed_detected = False
        for pred in result.get("predictions", []):
            if pred["class"] == "weed" and pred["confidence"] > 0.6:
                print("Weed detected with confidence:", pred["confidence"])
                weed_detected = True
                arduino.write(b'W')  # Send signal to Arduino to activate relay
                break  # Stop after the first weed detection

        # If no weed is detected, make sure the relay is deactivated
        if not weed_detected:
            print("No weed detected.")
            arduino.write(b'0')  # Send signal to deactivate relay

        # Get sensor readings from Arduino
        sensor_data = get_sensor_readings()

        # Return results including sensor data
        return jsonify({
            "result": result,
            "sensor_data": sensor_data
        })

    except Exception as e:
        os.remove(temp_file_path)
        return jsonify({'error': str(e)}), 500


def get_sensor_readings():
    """Function to retrieve sensor readings from Arduino"""
    # Send request to Arduino for sensor data
    arduino.write(b'S')  # Send signal 'S' to Arduino to fetch sensor data
    time.sleep(1)  # Wait for Arduino to send data

    # Read data from Arduino
    if arduino.in_waiting > 0:
        data = arduino.readline().decode('utf-8').strip()  # Read and decode sensor data
        print("Sensor Data from Arduino:", data)
        return parse_sensor_data(data)
    return {"moisture": "N/A", "temperature": "N/A", "humidity": "N/A"}

def parse_sensor_data(data):
    """Parse the sensor data received from Arduino"""
    try:
        # Assuming data format is: "Moisture: 500, Temperature: 22.5, Humidity: 60"
        sensor_values = data.split(", ")
        moisture = sensor_values[0].split(": ")[1]
        temperature = sensor_values[1].split(": ")[1]
        humidity = sensor_values[2].split(": ")[1]
        return {"moisture": moisture, "temperature": temperature, "humidity": humidity}
    except Exception as e:
        print("Error parsing sensor data:", e)
        return {"moisture": "N/A", "temperature": "N/A", "humidity": "N/A"}

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
