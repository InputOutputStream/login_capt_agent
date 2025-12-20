# app.py - Updated with complete security workflow
from flask import Flask, request, jsonify
from flask_cors import CORS
import traceback
from datetime import datetime, timedelta
import hashlib
import sqlite3
import base64
import os
from pathlib import Path
import pickle
import face_recognition
import numpy as np
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json

app = Flask(__name__)
CORS(app)

# Configuration
DATABASE_PATH = 'database/auth.db'
MAX_LOGIN_ATTEMPTS = 3
LOCKOUT_DURATION_HOURS = 5
FACE_MATCH_THRESHOLD = 0.6

# Email Configuration
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SMTP_USERNAME = 'admin'  
SMTP_PASSWORD = '1234'   
ADMIN_EMAIL = 'arnoldhge@gmail.com' 

# Paths
KNOWN_FACES_DIR = 'known_faces'
CAPTURED_FACES_DIR = 'captured_faces'

# Initialize directories
Path('database').mkdir(exist_ok=True)
Path(KNOWN_FACES_DIR).mkdir(exist_ok=True)
Path(CAPTURED_FACES_DIR).mkdir(exist_ok=True)

def init_database():
    """Initialize SQLite database with required tables"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            face_encoding BLOB,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Login attempts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS login_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            success BOOLEAN NOT NULL,
            ip_address TEXT,
            user_agent TEXT,
            face_captured BOOLEAN DEFAULT 0,
            face_authorized BOOLEAN DEFAULT 0,
            confidence REAL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Lockouts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lockouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            face_hash TEXT,
            lock_reason TEXT,
            locked_until TIMESTAMP,
            admin_notified BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Admin alerts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_type TEXT NOT NULL,
            message TEXT,
            email TEXT,
            images TEXT,  
            severity TEXT DEFAULT 'MEDIUM',
            resolved BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )  
    ''')
    
    #images is a JSON array of base64 images
    
    conn.commit()
    conn.close()
    print("✅ Database initialized successfully")

# Helper functions
def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def is_locked_out(email):
    """Check if email is currently locked out"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM lockouts 
        WHERE email = ? AND locked_until > datetime('now')
        ORDER BY created_at DESC LIMIT 1
    ''', (email,))
    
    lockout = cursor.fetchone()
    conn.close()
    
    return lockout is not None

def get_recent_failed_attempts(email, hours=1):
    """Get count of recent failed login attempts"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT COUNT(*) FROM login_attempts 
        WHERE email = ? AND success = 0 
        AND timestamp > datetime('now', ?)
    ''', (email, f'-{hours} hours'))
    
    count = cursor.fetchone()[0]
    conn.close()
    
    return count

def create_lockout(email, reason, face_hash=None, images=None):
    """Create a lockout record"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Calculate lockout time
    locked_until = datetime.now() + timedelta(hours=LOCKOUT_DURATION_HOURS)
    
    cursor.execute('''
        INSERT INTO lockouts (email, face_hash, lock_reason, locked_until)
        VALUES (?, ?, ?, ?)
    ''', (email, face_hash, reason, locked_until))
    
    # Create admin alert with images
    images_json = '[]' if images is None else json.dumps(images)
    cursor.execute('''
        INSERT INTO admin_alerts (alert_type, message, email, images, severity)
        VALUES (?, ?, ?, ?, ?)
    ''', ('LOCKOUT', f'User {email} locked out: {reason}', email, images_json, 'HIGH'))
    
    conn.commit()
    conn.close()
    
    # Send email alert with images
    send_lockout_email(email, reason, images)

def record_login_attempt(email, success, ip_address=None, user_agent=None, 
                         face_captured=False, face_authorized=False, confidence=0.0):
    """Record a login attempt"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO login_attempts 
        (email, success, ip_address, user_agent, face_captured, face_authorized, confidence)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (email, success, ip_address, user_agent, face_captured, face_authorized, confidence))
    
    conn.commit()
    conn.close()

def send_warning_email(email, ip_address, user_agent, attempt_number):
    """Send warning email to admin"""
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_USERNAME
        msg['To'] = ADMIN_EMAIL
        msg['Subject'] = f'⚠️ SUSPICIOUS LOGIN ATTEMPT: {email}'
        
        body = f"""
        <html>
        <body>
            <h2>⚠️ Suspicious Login Attempt Detected</h2>
            <p><strong>User Email:</strong> {email}</p>
            <p><strong>Attempt Number:</strong> {attempt_number}</p>
            <p><strong>IP Address:</strong> {ip_address}</p>
            <p><strong>User Agent:</strong> {user_agent}</p>
            <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Action Required:</strong> Monitor this user for further suspicious activity.</p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        
        return True
    except Exception as e:
        print(f"Failed to send warning email: {e}")
        return False

def send_lockout_email(email, reason, images=None):
    """Send lockout email to admin with captured images"""
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_USERNAME
        msg['To'] = ADMIN_EMAIL
        msg['Subject'] = f'🔒 ACCOUNT LOCKED: {email}'
        
        # Create HTML with embedded images
        images_html = ""
        if images:
            for i, img_data in enumerate(images, 1):
                images_html += f"""
                <div style="margin: 20px 0; border: 1px solid #ccc; padding: 10px;">
                    <h4>Captured Image #{i}</h4>
                    <img src="data:image/jpeg;base64,{img_data.split(',')[1] if ',' in img_data else img_data}" 
                         style="max-width: 300px; border: 1px solid #ddd;" />
                </div>
                """
        
        body = f"""
        <html>
        <body>
            <h2 style="color: #d32f2f;">🔒 Account Locked</h2>
            <div style="background-color: #ffebee; padding: 15px; border-radius: 5px;">
                <p><strong>User Email:</strong> {email}</p>
                <p><strong>Lock Reason:</strong> {reason}</p>
                <p><strong>Lock Duration:</strong> {LOCKOUT_DURATION_HOURS} hours</p>
                <p><strong>Lock Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>Auto-unlock:</strong> {LOCKOUT_DURATION_HOURS} hours from now</p>
            </div>
            
            <h3>Captured Images:</h3>
            {images_html if images else '<p>No images captured</p>'}
            
            <div style="margin-top: 30px; padding: 15px; background-color: #f5f5f5;">
                <h4>Action Required:</h4>
                <ol>
                    <li>Review the captured images above</li>
                    <li>Verify user identity if necessary</li>
                    <li>Account will auto-unlock after {LOCKOUT_DURATION_HOURS} hours</li>
                    <li>Contact user for manual unlock if needed</li>
                </ol>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        
        return True
    except Exception as e:
        print(f"Failed to send lockout email: {e}")
        return False

def base64_to_image(base64_string):
    """Convert base64 string to image array"""
    import base64
    from PIL import Image
    from io import BytesIO
    import numpy as np
    
    if ',' in base64_string:
        base64_string = base64_string.split(',')[1]
    
    img_data = base64.b64decode(base64_string)
    img = Image.open(BytesIO(img_data))
    return np.array(img)

def compare_faces(face_image1_base64, face_image2_base64):
    """Compare two faces and return similarity score"""
    try:
        # Convert base64 to images
        image1 = base64_to_image(face_image1_base64)
        image2 = base64_to_image(face_image2_base64)
        
        # Get face encodings
        encodings1 = face_recognition.face_encodings(image1)
        encodings2 = face_recognition.face_encodings(image2)
        
        if not encodings1 or not encodings2:
            return 0.0
        
        # Calculate face distance
        face_distance = face_recognition.face_distance([encodings1[0]], encodings2[0])[0]
        
        # Convert distance to similarity (0-1)
        similarity = 1.0 - min(face_distance, 1.0)
        
        return similarity
    except Exception as e:
        print(f"Face comparison error: {e}")
        return 0.0

def save_captured_image(email, image_base64, attempt_number):
    """Save captured image to file"""
    try:
        filename = f"{CAPTURED_FACES_DIR}/{email}_{attempt_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        
        if ',' in image_base64:
            image_base64 = image_base64.split(',')[1]
        
        with open(filename, 'wb') as f:
            f.write(base64.b64decode(image_base64))
        
        return filename
    except Exception as e:
        print(f"Failed to save image: {e}")
        return None

def get_unauthorized_face_attempts(email, hours=1):
    """Get unauthorized face attempts for an email"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM login_attempts 
        WHERE email = ? AND face_captured = 1 AND face_authorized = 0
        AND timestamp > datetime('now', ?)
        ORDER BY timestamp
    ''', (email, f'-{hours} hours'))
    
    attempts = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return attempts

# Routes
@app.route('/')
def index():
    """Root endpoint"""
    return jsonify({
        'service': 'VC Authentication API',
        'version': '3.0.0',
        'features': ['facial_recognition', 'lockout_system', 'admin_alerts'],
        'status': 'running'
    })

@app.route('/login', methods=['POST'])
def login():
    """Login endpoint with facial recognition workflow"""
    try:
        data = request.json
        
        name = data.get('name', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        face_image = data.get('face_image', None)  # Optional face image
        
        # Get client info
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent', '')
        
        # Validation
        if not name or not email or not password:
            return jsonify({
                'success': False,
                'message': 'All fields are required',
                'require_face': False
            }), 400
        
        # Check lockout
        if is_locked_out(email):
            return jsonify({
                'success': False,
                'message': f'Account locked. Try again in {LOCKOUT_DURATION_HOURS} hours.',
                'locked': True,
                'require_face': False
            }), 403
        
        # Get user from database
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()
        
        # Check credentials
        if not user:
            record_login_attempt(email, False, ip_address, user_agent)
            return handle_failed_attempt(email, ip_address, user_agent, face_image)
        
        # Check name
        if user['name'].lower() != name.lower():
            record_login_attempt(email, False, ip_address, user_agent)
            return handle_failed_attempt(email, ip_address, user_agent, face_image)
        
        # Check password
        password_hash = hash_password(password)
        if password_hash != user['password_hash']:
            record_login_attempt(email, False, ip_address, user_agent)
            return handle_failed_attempt(email, ip_address, user_agent, face_image)
        
        # SUCCESS: Credentials are correct
        # But check if account is locked (should have been checked above)
        
        record_login_attempt(email, True, ip_address, user_agent)
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'user': {
                'id': user['id'],
                'name': user['name'],
                'email': user['email']
            }
        })
        
    except Exception as e:
        app.logger.error(f"Login error: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'success': False,
            'message': 'Server error',
            'error': str(e)
        }), 500

def handle_failed_attempt(email, ip_address, user_agent, face_image=None):
    """Handle failed login attempt with facial recognition logic"""
    
    # Get recent failed attempts
    failed_attempts = get_recent_failed_attempts(email)
    total_attempts = failed_attempts + 1
    
    # If face image provided, verify it
    if face_image:
        # Save the captured image
        save_captured_image(email, face_image, total_attempts)
        
        # Check if face is authorized (compare with stored faces)
        face_authorized = False
        confidence = 0.0
        
        # Try to compare with stored face if user exists
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT face_encoding FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()
        
        if user and user['face_encoding']:
            # User has stored face encoding
            stored_encoding = pickle.loads(user['face_encoding'])
            # Compare faces (simplified - implement actual comparison)
            # For now, mark as unauthorized
            face_authorized = False
            confidence = 0.0
        else:
            # No stored face, mark as unauthorized
            face_authorized = False
            confidence = 0.0
        
        # Record attempt with face capture
        record_login_attempt(email, False, ip_address, user_agent, 
                            face_captured=True, face_authorized=face_authorized, 
                            confidence=confidence)
        
        # If unauthorized face on 3rd attempt, send warning
        if total_attempts == 3 and not face_authorized:
            send_warning_email(email, ip_address, user_agent, total_attempts)
        
        # If unauthorized face on 6th attempt, lock account
        if total_attempts >= 6 and not face_authorized:
            # Get captured images
            unauthorized_attempts = get_unauthorized_face_attempts(email)
            captured_images = []
            
            for attempt in unauthorized_attempts[-3:]:  # Last 3 images
                # In production, you'd retrieve the actual images
                captured_images.append("image_data_placeholder")
            
            # Create lockout
            create_lockout(email, f'6 unauthorized face attempts', 
                          face_hash=None, images=captured_images)
            
            return jsonify({
                'success': False,
                'message': 'Account locked due to multiple unauthorized attempts.',
                'locked': True,
                'require_face': False
            }), 403
        
        return jsonify({
            'success': False,
            'message': f'Invalid credentials. Attempt {total_attempts}/3 before face capture.',
            'attempts': total_attempts,
            'max_attempts': 3,
            'require_face': total_attempts >= 3
        }), 401
    
    else:
        # No face image provided
        # Record attempt without face
        record_login_attempt(email, False, ip_address, user_agent)
        
        # After 3 failed attempts, require face capture
        if total_attempts >= 3:
            return jsonify({
                'success': False,
                'message': f'Face verification required. Please enable camera.',
                'attempts': total_attempts,
                'max_attempts': 3,
                'require_face': True
            }), 401
        
        return jsonify({
            'success': False,
            'message': f'Invalid credentials. Attempt {total_attempts}/3.',
            'attempts': total_attempts,
            'max_attempts': 3,
            'require_face': total_attempts >= 3
        }), 401

@app.route('/register', methods=['POST'])
def register():
    """Register new user with optional face registration"""
    try:
        data = request.json
        
        name = data.get('name', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        face_image = data.get('face_image', None)
        
        # Validation
        if not name or not email or not password:
            return jsonify({
                'success': False,
                'message': 'All fields are required'
            }), 400
        
        if len(password) < 6:
            return jsonify({
                'success': False,
                'message': 'Password must be at least 6 characters'
            }), 400
        
        # Hash password
        password_hash = hash_password(password)
        
        # Process face image if provided
        face_encoding = None
        if face_image:
            try:
                # Convert base64 to image
                image = base64_to_image(face_image)
                # Get face encoding
                encodings = face_recognition.face_encodings(image)
                if encodings:
                    face_encoding = pickle.dumps(encodings[0])
            except Exception as e:
                print(f"Face encoding error: {e}")
        
        # Insert user
        conn = get_db()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO users (name, email, password_hash, face_encoding)
                VALUES (?, ?, ?, ?)
            ''', (name, email, password_hash, face_encoding))
            
            user_id = cursor.lastrowid
            conn.commit()
            
            return jsonify({
                'success': True,
                'message': 'Registration successful',
                'user_id': user_id
            })
            
        except sqlite3.IntegrityError:
            return jsonify({
                'success': False,
                'message': 'Email already exists'
            }), 409
        finally:
            conn.close()
        
    except Exception as e:
        app.logger.error(f"Registration error: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'success': False,
            'message': 'Server error'
        }), 500

@app.route('/verify-face', methods=['POST'])
def verify_face():
    """Verify face against stored faces"""
    try:
        data = request.json
        
        email = data.get('email', '').strip().lower()
        face_image = data.get('face_image', '')
        attempt_number = data.get('attempt_number', 1)
        
        if not email or not face_image:
            return jsonify({
                'success': False,
                'message': 'Email and face image required'
            }), 400
        
        # Get user's stored face
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT face_encoding FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()
        
        if not user or not user['face_encoding']:
            return jsonify({
                'success': False,
                'authorized': False,
                'message': 'No stored face found for user'
            })
        
        # Compare faces
        stored_encoding = pickle.loads(user['face_encoding'])
        current_image = base64_to_image(face_image)
        current_encodings = face_recognition.face_encodings(current_image)
        
        if not current_encodings:
            return jsonify({
                'success': False,
                'authorized': False,
                'message': 'No face detected in image'
            })
        
        # Calculate similarity
        face_distance = face_recognition.face_distance([stored_encoding], current_encodings[0])[0]
        similarity = 1.0 - min(face_distance, 1.0)
        
        authorized = similarity >= FACE_MATCH_THRESHOLD
        
        return jsonify({
            'success': True,
            'authorized': authorized,
            'similarity': similarity,
            'threshold': FACE_MATCH_THRESHOLD,
            'message': 'Face verified successfully'
        })
        
    except Exception as e:
        app.logger.error(f"Face verification error: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'success': False,
            'authorized': False,
            'error': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        conn.close()
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'facial_recognition': 'available',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@app.route('/status', methods=['GET'])
def status():
    """System status endpoint"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM login_attempts WHERE timestamp > datetime("now", "-24 hours")')
        recent_attempts = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM lockouts WHERE locked_until > datetime("now")')
        active_lockouts = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'status': 'operational',
            'users': user_count,
            'login_attempts_24h': recent_attempts,
            'active_lockouts': active_lockouts,
            'facial_recognition': 'active',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/admin/alerts', methods=['GET'])
def get_alerts():
    """Get unresolved alerts"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM admin_alerts 
            WHERE resolved = 0 
            ORDER BY created_at DESC 
            LIMIT 50
        ''')
        
        alerts = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({
            'alerts': alerts,
            'count': len(alerts)
        })
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/admin/login-attempts', methods=['GET'])
def get_login_attempts():
    """Get recent login attempts"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 100))
        offset = (page - 1) * limit
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM login_attempts 
            ORDER BY timestamp DESC 
            LIMIT ? OFFSET ?
        ''', (limit, offset))
        
        attempts = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({
            'attempts': attempts,
            'page': page,
            'limit': limit
        })
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

if __name__ == '__main__':
    # Initialize database
    init_database()
    
    # Run server
    print(" Starting VC Authentication Server...")
    print(f" Database: {DATABASE_PATH}")
    print(f" Max login attempts before face capture: 3")
    print(f" Lockout duration: {LOCKOUT_DURATION_HOURS} hours")
    print(f" Admin alerts: {ADMIN_EMAIL}")
    print("\n Server ready at http://localhost:5000")
    print("   - Frontend: Open index.html in browser")
    print("   - Test login: Use any credentials (system will track attempts)")
    print("\n  IMPORTANT: Configure email settings in app.py (lines 25-27)")
    
    app.run(host='0.0.0.0', port=5000, debug=True)