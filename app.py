from flask import Flask, request, render_template_string, send_from_directory, jsonify
import os
import time
import json
import requests
from datetime import datetime
import tensorflow as tf
from tensorflow.keras.preprocessing import image
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
import numpy as np
import pandas as pd

# Load your model
model = tf.keras.models.load_model('smart_trash_model.h5')

# Class indices
class_indices = {
    'Organic': 0,
    'Other': 1,
    'Plastic': 2
}

# Counters for each trash type
trash_counters = {
    'Organic': 0,
    'Other': 0,
    'Plastic': 0,
    'history': [],  # To store historical data for time-based charts
    'hourly_data': {}  # To store hourly submission counts
}

# Track the latest prediction
latest_prediction = {
    'label': 'None',
    'timestamp': 'No prediction yet',
    'confidence': 0
}

# Path to store counter data for Streamlit
DATA_FILE = 'trash_data.json'

# # Ubidots configuration
# UBIDOTS_TOKEN = "BBUS-2CnMsYYSV9hgXRjc6lTgCKZYi9dECy"  # Replace with your actual token
# DEVICE_LABEL = "smart_trash_classifier"  # Device label for Ubidots
# VARIABLE_LABELS = {
#     'Organic': "organic_count",
#     'Other': "other_count",
#     'Plastic': "plastic_count",
#     'hourly_submissions': "hourly_submissions"  # New variable for hourly submission tracking
# }

app = Flask(__name__)

def predict_image(filepath, model, class_indices):
    """Predict the class of an image using the model"""
    img = image.load_img(filepath, target_size=(224, 224))
    img_array = image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = preprocess_input(img_array)
    
    prediction = model.predict(img_array)
    predicted_class_index = np.argmax(prediction)
    confidence = float(prediction[0][predicted_class_index])
    predicted_label = list(class_indices.keys())[list(class_indices.values()).index(predicted_class_index)]
    return predicted_label, confidence

# def send_to_ubidots(trash_type=None, hourly_data=None):
#     """Send data to Ubidots"""
#     # Create the URL for the HTTP request
#     url = "http://industrial.api.ubidots.com/api/v1.6/devices/{}".format(DEVICE_LABEL)
    
#     # Create the headers for the HTTP request
#     headers = {"X-Auth-Token": UBIDOTS_TOKEN, "Content-Type": "application/json"}
    
#     # Create the payload
#     payload = {}
    
#     if trash_type:
#         # Add specific trash counter
#         variable_label = VARIABLE_LABELS[trash_type]
#         payload[variable_label] = trash_counters[trash_type]
#         print(f"Sending to Ubidots: {trash_type} = {trash_counters[trash_type]}")
    
#     if hourly_data:
#         # Add hourly submission data
#         current_hour = datetime.now().strftime('%Y-%m-%d %H:00')
#         payload[VARIABLE_LABELS['hourly_submissions']] = hourly_data.get(current_hour, 0)
#         print(f"Sending to Ubidots: hourly_submissions = {hourly_data.get(current_hour, 0)}")
    
#     if not payload:
#         return False
    
#     # Make the HTTP request
#     status = 400
#     attempts = 0
#     while status >= 400 and attempts <= 5:
#         req = requests.post(url=url, headers=headers, json=payload)
#         status = req.status_code
#         attempts += 1
#         time.sleep(1)
    
#     # Process results
#     print("Ubidots response:", status, req.text)
#     if status >= 400:
#         print(f"[ERROR] Could not send data to Ubidots after 5 attempts")
#         return False
    
#     print(f"[INFO] Data sent to Ubidots successfully")
#     return True

def update_hourly_data(timestamp):
    """Update hourly submission data"""
    # Format timestamp to hourly granularity (YYYY-MM-DD HH:00)
    hour_key = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:00')
    
    # Initialize if not exists
    if hour_key not in trash_counters['hourly_data']:
        trash_counters['hourly_data'][hour_key] = {
            'total': 0,
            'Organic': 0,
            'Other': 0,
            'Plastic': 0
        }
    
    # Increment counters
    trash_counters['hourly_data'][hour_key]['total'] += 1
    
    # Return the current hour's data
    return trash_counters['hourly_data']

def save_counter_data():
    """Save counter data to a JSON file for Streamlit to read"""
    with open(DATA_FILE, 'w') as f:
        json.dump(trash_counters, f)
    print(f"Counter data saved to {DATA_FILE}")

# Create directory for uploads if it doesn't exist
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Load existing counter data if available
if os.path.exists(DATA_FILE):
    try:
        with open(DATA_FILE, 'r') as f:
            trash_counters = json.load(f)
        print(f"Loaded counter data from {DATA_FILE}")
    except:
        print(f"Could not load counter data from {DATA_FILE}")

@app.route('/')
def index():
    return "Flask server is running. Please use the Streamlit dashboard for visualization."

@app.route('/api/counters', methods=['GET'])
def get_counters():
    """API endpoint to get the current counters"""
    return jsonify(trash_counters)

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'image/jpeg' in request.headers.get('Content-Type', ''):
        timestamp = int(time.time())
        filename = f'esp32cam_{timestamp}.jpg'
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        # Save the image to disk
        with open(filepath, 'wb') as f:
            f.write(request.data)

        try:
            # Predict the label
            predicted_label, confidence = predict_image(filepath, model, class_indices)
            
            # Update the latest prediction
            latest_prediction['label'] = predicted_label
            latest_prediction['confidence'] = round(confidence * 100, 2)  # Convert to percentage
            latest_prediction['timestamp'] = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
            
            # Increment the counter for the predicted class
            trash_counters[predicted_label] += 1
            
            # Update hourly data
            hourly_data = update_hourly_data(timestamp)
            hourly_data[datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:00')][predicted_label] += 1
            
            # Add to history for time-based charts
            history_entry = {
                'timestamp': datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S'),
                'Organic': trash_counters['Organic'],
                'Other': trash_counters['Other'],
                'Plastic': trash_counters['Plastic'],
                'prediction': predicted_label
            }
            trash_counters['history'].append(history_entry)
            
            # Keep history to a reasonable size (last 100 entries)
            if len(trash_counters['history']) > 100:
                trash_counters['history'] = trash_counters['history'][-100:]
            
            # Save counter data for Streamlit
            save_counter_data()
            
            # Send data to Ubidots, NOT USED IN FINAL PROTO!
            # send_to_ubidots(predicted_label, hourly_data)
            
            # Create a new filename with the predicted label
            new_filename = f'{timestamp}_{predicted_label}.jpg'
            new_filepath = os.path.join(UPLOAD_FOLDER, new_filename)

            # Rename the file
            os.rename(filepath, new_filepath)

            # Print the current counters and latest prediction
            print(f"Current trash counts: Organic={trash_counters['Organic']}, Other={trash_counters['Other']}, Plastic={trash_counters['Plastic']}")
            print(f"Latest prediction: {predicted_label} with {latest_prediction['confidence']}% confidence")
            
            # Return the predicted label as a response
            return predicted_label, 200

        except Exception as e:
            # Handle any errors that occur during prediction or file renaming
            print(f"Error processing image: {str(e)}")
            return f'Error: {str(e)}', 500

    return 'Unsupported media type', 415

@app.route('/static/uploads/<filename>')
def serve_image(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/reset_counters', methods=['GET'])
def reset_counters():
    """Reset all trash counters to zero"""
    for key in trash_counters:
        if key != 'history' and key != 'hourly_data':
            trash_counters[key] = 0
    
    # Clear history but keep hourly_data for long-term analytics
    trash_counters['history'] = []
    
    # Save counter data for Streamlit
    save_counter_data()
    
    # For reset, we'll send all counters to ensure Ubidots is fully updated
    # for trash_type in ['Organic', 'Other', 'Plastic']:
    #     send_to_ubidots(trash_type)
    
    return "Counters reset successfully", 200

if __name__ == '__main__':
    print(f"Server started. Images will be saved to {os.path.abspath(UPLOAD_FOLDER)}")
    print(f"Counter data will be saved to {os.path.abspath(DATA_FILE)} for Streamlit")
    # print("Ubidots integration enabled. Trash type and hourly submission data will be sent to Ubidots.")
    # Use host='0.0.0.0' to make the server accessible from other devices on the network
    app.run(host='0.0.0.0', port=5000, debug=True)