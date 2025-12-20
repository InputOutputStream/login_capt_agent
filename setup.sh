#!/bin/bash

echo "=== Setting up VC Security System ==="

# Create required directories
mkdir -p database known_faces captured_faces

# Update app.py with your email credentials
echo "Please update email settings in app.py:"
echo "1. SMTP_USERNAME = 'your-email@gmail.com'"
echo "2. SMTP_PASSWORD = 'your-app-password'"
echo "3. ADMIN_EMAIL = 'admin@yourcompany.com'"

# Install Python dependencies
pip install flask flask-cors opencv-python face_recognition pillow

# Initialize database
python3 -c "
import sqlite3
conn = sqlite3.connect('database/auth.db')
cursor = conn.cursor()
cursor.execute('SELECT name FROM sqlite_master WHERE type=\"table\"')
print('Tables:', cursor.fetchall())
conn.close()
"

echo ""
echo "=== Setup Complete ==="
echo "To start the system:"
echo "1. Update email settings in app.py"
echo "2. Run: python app.py"
echo "3. Open index.html in browser"
echo ""
echo "Test users are created automatically on first registration attempt."