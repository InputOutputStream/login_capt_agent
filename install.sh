#!/bin/bash

echo "=== Setting up Facial Recognition Auth System ==="

# Update system
echo "Updating system packages..."
sudo apt-get update -y

# Install Python and pip
echo "Installing Python and pip..."
sudo apt-get install -y python3 python3-pip python3-venv

# Install system dependencies for OpenCV and MediaPipe
echo "Installing system dependencies..."
sudo apt-get install -y libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev
sudo apt-get install -y libgstreamer1.0-0 gstreamer1.0-plugins-base gstreamer1.0-plugins-good

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv

# Activate virtual environment and install Python packages
echo "Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip

# Install backend dependencies
echo "Installing backend dependencies..."
pip install flask flask-cors opencv-python mediapipe numpy pillow scikit-learn
pip install smtplib email-validator sqlalchemy

# Install face_recognition library (alternative to MediaPipe for recognition)
echo "Installing face_recognition library..."
pip install face_recognition dlib cmake

# Create necessary directories
echo "Creating project directories..."
mkdir -p frontend backend database known_faces captured_faces

# Create requirements.txt
echo "Creating requirements.txt..."
pip freeze > backend/requirements.txt

# Set permissions
chmod +x install.sh

echo "=== Installation Complete ==="echo ""
echo "To start the system:"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Start backend: cd backend && python app.py"
echo "3. Open frontend/index.html in browser"
echo ""