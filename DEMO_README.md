# Smart Dustbin - Waste Classification Demo 🗑️♻️

## Overview

This project adds a web-based demo page to test the waste image classification system for the smart dustbin IoT project. The demo interface allows you to upload images and instantly see AI-based classification results.

## New Files Added

### 1. **demo.html** - Web Interface
An interactive single-page application for testing waste classification:
- **Image Upload**: Drag-and-drop or click to upload waste images
- **Real-time Preview**: View the image before classification
- **AI Classification**: Sends image to server for classification
- **Results Display**: Shows category (Organic/Recyclable) with confidence score
- **Responsive Design**: Works on desktop and mobile devices

### 2. **server.py** - Flask Backend
A Flask-based web server that:
- Serves the demo.html page
- Handles image upload and classification requests
- Provides multiple API endpoints
- Includes mock classification for testing (ready for real ML model integration)
- Has built-in error handling and validation

### 3. **requirements.txt** - Python Dependencies
Contains all required Python packages for running the server.

---

## Setup & Installation

### Prerequisites
- Python 3.7 or higher
- pip (Python package manager)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Configure Server IP (Optional)
If running the server on a different machine, update the ESP32-CAM configuration:

In `esp32_cam.py`, change:
```python
SERVER_URL = "http://192.168.1.100:5000/classify"
```
Replace `192.168.1.100` with your server's IP address.

### Step 3: Run the Server
```bash
python server.py
```

You should see:
```
╔═══════════════════════════════════════════════════════════════╗
║     Smart Dustbin - Waste Classification Server               ║
║                  v1.0                                         ║
╚═══════════════════════════════════════════════════════════════╝

📍 Demo Page: http://localhost:5000/
📍 API Endpoint: http://localhost:5000/classify
📍 Health Check: http://localhost:5000/api/health
📍 Status: http://localhost:5000/api/status

Ready to classify waste images! 🤖♻️
```

---

## Usage

### Web Demo Interface
1. Open your browser and go to: **http://localhost:5000/**
2. Upload a waste image (PNG, JPG, JPEG, GIF, or BMP)
3. Click **"Classify Image"** button
4. View the classification result (Organic or Recyclable) with confidence percentage
5. Try another image with **"Clear & Upload New"** button

### API Endpoints

#### 1. **GET /** or **/demo**
Serves the interactive demo page.

```
GET http://localhost:5000/
```

#### 2. **POST /classify**
Classifies a waste image.

```
curl -X POST -F "image=@photo.jpg" http://localhost:5000/classify
```

**Response:**
```json
{
  "success": true,
  "category": "organic",
  "confidence": 0.892,
  "message": "Image classified as organic with 89.2% confidence"
}
```

#### 3. **GET /api/health**
Health check endpoint.

```
GET http://localhost:5000/api/health
```

**Response:**
```json
{
  "status": "ok",
  "service": "Smart Dustbin Classification Server",
  "version": "1.0",
  "model_loaded": false
}
```

#### 4. **GET /api/status**
Server status and capabilities.

```
GET http://localhost:5000/api/status
```

---

## Features

### Demo Page Capabilities
✅ Drag-and-drop file upload  
✅ Image preview before classification  
✅ Real-time classification results  
✅ Confidence score display  
✅ Category descriptions  
✅ Mobile-responsive design  
✅ Clean, modern UI  

### Server Features
✅ File upload validation  
✅ Multiple file format support (PNG, JPG, JPEG, GIF, BMP)  
✅ Max 16MB file size limit  
✅ JSON API responses  
✅ Comprehensive error handling  
✅ Health check endpoint  
✅ Uploaded files saved for future analysis  

---

## Classification Categories

### 🟢 **Organic Waste**
- Food scraps, peels, leftovers
- Leaves, flowers, plant matter
- Paper (clean, untreated)
- Other biodegradable materials

### 🟠 **Recyclable Waste**
- Plastic bottles and containers
- Metal cans and aluminum
- Glass bottles and jars
- Cardboard and newspaper

---

## Integration with ESP32-CAM

The ESP32-CAM automatically sends captured images to this server:

```python
# From esp32_cam.py
SERVER_URL = "http://192.168.1.100:5000/classify"

# Image is sent as multipart form-data
response = urequests.post(SERVER_URL, headers=headers, data=payload)
```

The server's response is published to MQTT:
```
Topic: shubham0123/feeds/waste-category
Message: "organic" or "recyclable"
```

This controls the servo motor to sort waste automatically!

---

## Advanced: Adding a Real ML Model

To use a trained machine learning model instead of mock classification:

### Option 1: TensorFlow/Keras Model
```python
# In server.py, uncomment and modify:
from tensorflow.keras.models import load_model

MODEL_PATH = 'waste_classification_model.h5'
model = load_model(MODEL_PATH)

def classify_image(image_path):
    img = load_img(image_path, target_size=(224, 224))
    img_array = img_to_array(img) / 255.0
    prediction = model.predict(np.array([img_array]))
    # Process prediction...
```

### Option 2: OpenCV + scikit-learn
```python
# Install additional package:
pip install opencv-python scikit-learn
```

### Model Training Tips
- Use Google Colab or Kaggle for free GPU access
- Popular datasets: 
  - Waste Classification Dataset (Kaggle)
  - TACO Dataset
  - TrashNet Dataset

---

## Troubleshooting

### Issue: "Address already in use" error
**Solution:** Change the port in server.py:
```python
app.run(host='0.0.0.0', port=5001)  # Use 5001 instead of 5000
```

### Issue: Module not found errors
**Solution:** Reinstall dependencies:
```bash
pip install --upgrade -r requirements.txt
```

### Issue: ESP32 can't connect to server
**Solution:** 
1. Check server IP: `ipconfig` (Windows) or `ifconfig` (Linux/Mac)
2. Ensure firewall allows port 5000
3. Verify both devices are on the same WiFi network

### Issue: Image upload fails
**Solution:**
- Check file size (max 16MB)
- Use supported format (PNG, JPG, JPEG, GIF, BMP)
- Ensure `/uploads` folder has write permissions

---

## File Structure
```
smart_dustbin_iot/
├── demo.html           # Web interface for testing
├── server.py           # Flask backend server
├── requirements.txt    # Python dependencies
├── esp32_cam.py        # ESP32 camera module
├── main.py             # Main dustbin controller
├── config.py           # Configuration credentials
├── boot.py             # Boot script
└── uploads/            # Uploaded images (auto-created)
```

---

## License & Credits

Part of the Smart Dustbin IoT project for automated waste classification and sorting.

**Technologies Used:**
- Flask (Web framework)
- HTML5 + CSS3 + JavaScript (Frontend)
- Python (Backend)
- ESP32-CAM (IoT device)
- MQTT (IoT communication)

---

## Support & Next Steps

1. **Test the demo page** with various waste images
2. **Fine-tune classification** by training your own ML model
3. **Deploy to cloud** (AWS, Azure, Google Cloud) for remote access
4. **Add more categories** (metal, plastic, glass) as needed
5. **Implement MQTT publishing** to automate servo control

Enjoy automated waste sorting! ♻️🤖
