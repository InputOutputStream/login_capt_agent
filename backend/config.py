import os
from datetime import timedelta

class Config:
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here-change-in-production'
    
    # Database
    DATABASE_PATH = '../database/database.db'
    
    # Security
    MAX_LOGIN_ATTEMPTS = 3
    LOCKOUT_DURATION = timedelta(hours=5)
    FACE_MATCH_THRESHOLD = 0.6  # Lower = more strict
    
    # Email
    SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
    SMTP_USERNAME = os.environ.get('SMTP_USERNAME', 'your-email@gmail.com')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', 'your-app-password')
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@yourcompany.com')
    
    # File paths
    KNOWN_FACES_DIR = '../known_faces'
    CAPTURED_FACES_DIR = '../captured_faces'
    
    # Face recognition
    USE_MEDIAPIPE = False  # Set to False to use face_recognition library
    FACE_DETECTION_CONFIDENCE = 0.5
    
    # Logging
    LOG_FILE = '../auth_system.log'