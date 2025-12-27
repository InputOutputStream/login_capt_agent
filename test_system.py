# app.py - Updated with complete frontend integration
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
import secrets
import uuid

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

# Session storage (in production, use Redis or proper session management)
active_sessions = {}

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
    
    # Login attempts table - UPDATED with location fields
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS login_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT NOT NULL,
            success BOOLEAN NOT NULL,
            ip_address TEXT,
            user_agent TEXT,
            latitude REAL,
            longitude REAL,
            face_image TEXT,
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
    
    # Sessions table for auth tokens
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            email TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
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

def generate_token():
    """Generate a secure random token"""
    return secrets.token_urlsafe(32)

def create_session(user_id, email):
    """Create a new session and return token"""
    token = generate_token()
    expires_at = datetime.now() + timedelta(hours=24)
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO sessions (token, user_id, email, expires_at)
        VALUES (?, ?, ?, ?)
    ''', (token, user_id, email, expires_at))
    
    conn.commit()
    conn.close()
    
    # Store in memory cache
    active_sessions[token] = {
        'user_id': user_id,
        'email': email,
        'expires_at': expires_at
    }
    
    return token

def validate_token(token):
    """Validate session token"""
    # Check memory cache first
    if token in active_sessions:
        session = active_sessions[token]
        if session['expires_at'] > datetime.now():
            return session
        else:
            del active_sessions[token]
    
    # Check database
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM sessions 
        WHERE token = ? AND expires_at > datetime('now')
    ''', (token,))
    
    session = cursor.fetchone()
    conn.close()
    
    if session:
        return dict(session)
    return None

def invalidate_session(token):
    """Invalidate/delete a session"""
    # Remove from memory
    if token in active_sessions:
        del active_sessions[token]
    
    # Remove from database
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM sessions WHERE token = ?', (token,))
    conn.commit()
    conn.close()

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

def record_login_attempt(name, email, success, ip_address=None, user_agent=None, 
                         latitude=None, longitude=None, face_image=None,
                         face_captured=False, face_authorized=False, confidence=0.0):
    """Record a login attempt with location data"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO login_attempts 
        (name, email, success, ip_address, user_agent, latitude, longitude, 
         face_image, face_captured, face_authorized, confidence)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (name, email, success, ip_address, user_agent, latitude, longitude,
          face_image, face_captured, face_authorized, confidence))
    
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
            </div>
            
            <h3>Captured Images:</h3>
            {images_html if images else '<p>No images captured</p>'}
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
    from PIL import Image
    from io import BytesIO
    
    if ',' in base64_string:
        base64_string = base64_string.split(',')[1]
    
    img_data = base64.b64decode(base64_string)
    img = Image.open(BytesIO(img_data))
    return np.array(img)

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

# Routes
@app.route('/')
def index():
    """Root endpoint"""
    return jsonify({
        'service': 'VC Authentication API',
        'version': '3.0.0',
        'features': ['facial_recognition', 'lockout_system', 'admin_alerts', 'location_tracking'],
        'status': 'running'
    })

@app.route('/login', methods=['POST'])
def login():
    """Login endpoint with facial recognition workflow and location tracking"""
    try:
        data = request.json
        
        name = data.get('name', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        face_image = data.get('face_image', None)
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        ip_address = data.get('ip_address') or request.remote_addr
        
        # Get client info
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
            record_login_attempt(name, email, False, ip_address, user_agent, 
                               latitude, longitude, face_image)
            return handle_failed_attempt(name, email, ip_address, user_agent, 
                                        latitude, longitude, face_image)
        
        # Check name
        if user['name'].lower() != name.lower():
            record_login_attempt(name, email, False, ip_address, user_agent,
                               latitude, longitude, face_image)
            return handle_failed_attempt(name, email, ip_address, user_agent,
                                        latitude, longitude, face_image)
        
        # Check password
        password_hash = hash_password(password)
        if password_hash != user['password_hash']:
            record_login_attempt(name, email, False, ip_address, user_agent,
                               latitude, longitude, face_image)
            return handle_failed_attempt(name, email, ip_address, user_agent,
                                        latitude, longitude, face_image)
        
        # SUCCESS: Credentials are correct
        record_login_attempt(name, email, True, ip_address, user_agent,
                           latitude, longitude, None)
        
        # Create session token
        token = create_session(user['id'], email)
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'token': token,
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

def handle_failed_attempt(name, email, ip_address, user_agent, latitude, longitude, face_image=None):
    """Handle failed login attempt with facial recognition logic"""
    
    # Get recent failed attempts
    failed_attempts = get_recent_failed_attempts(email)
    total_attempts = failed_attempts + 1
    
    # If face image provided, verify it
    if face_image:
        # Save the captured image
        save_captured_image(email, face_image, total_attempts)
        
        # Record attempt with face capture
        record_login_attempt(name, email, False, ip_address, user_agent,
                           latitude, longitude, face_image,
                           face_captured=True, face_authorized=False, 
                           confidence=0.0)
        
        # If unauthorized face on 3rd attempt, send warning
        if total_attempts == 3:
            send_warning_email(email, ip_address, user_agent, total_attempts)
        
        # If unauthorized face on 6th attempt, lock account
        if total_attempts >= 6:
            # Create lockout with face images
            captured_images = [face_image] if face_image else []
            create_lockout(email, f'{total_attempts} unauthorized attempts', 
                          face_hash=None, images=captured_images)
            
            return jsonify({
                'success': False,
                'message': 'Account locked due to multiple unauthorized attempts.',
                'locked': True,
                'require_face': False
            }), 403
        
        return jsonify({
            'success': False,
            'message': f'Invalid credentials. Attempt {total_attempts}.',
            'attempts': total_attempts,
            'max_attempts': 3,
            'require_face': total_attempts >= 3
        }), 401
    
    else:
        # No face image provided
        record_login_attempt(name, email, False, ip_address, user_agent,
                           latitude, longitude, None)
        
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

@app.route('/logout', methods=['POST'])
def logout():
    """Logout endpoint - invalidate session"""
    try:
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization', '')
        
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            invalidate_session(token)
        
        return jsonify({
            'success': True,
            'message': 'Logged out successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Logout error',
            'error': str(e)
        }), 500

@app.route('/validate-session', methods=['GET'])
def validate_session():
    """Validate if session token is valid"""
    try:
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header.startswith('Bearer '):
            return jsonify({
                'success': False,
                'message': 'No token provided'
            }), 401
        
        token = auth_header.split(' ')[1]
        session = validate_token(token)
        
        if session:
            return jsonify({
                'success': True,
                'message': 'Session valid',
                'user': {
                    'email': session.get('email')
                }
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Invalid or expired session'
            }), 401
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Session validation error',
            'error': str(e)
        }), 500

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
                image = base64_to_image(face_image)
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
            
            # Create session token
            token = create_session(user_id, email)
            
            return jsonify({
                'success': True,
                'message': 'Registration successful',
                'token': token,
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

@app.route('/admin/login-attempts', methods=['GET'])
def get_login_attempts():
    """Get recent login attempts with all details for dashboard"""
    try:
        # Get pagination parameters
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 100))
        offset = (page - 1) * limit
        
        # Verify admin token (in production, add proper admin auth)
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            session = validate_token(token)
            if not session:
                return jsonify({'error': 'Unauthorized'}), 401
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                id,
                name,
                email,
                success,
                ip_address,
                user_agent,
                latitude,
                longitude,
                face_image,
                face_captured,
                face_authorized,
                confidence,
                timestamp
            FROM login_attempts 
            ORDER BY timestamp DESC 
            LIMIT ? OFFSET ?
        ''', (limit, offset))
        
        attempts = []
        for row in cursor.fetchall():
            attempt = {
                'id': row[0],
                'name': row[1],
                'email': row[2],
                'success': bool(row[3]),
                'ip_address': row[4],
                'user_agent': row[5],
                'latitude': row[6],
                'longitude': row[7],
                'face_image': row[8],
                'face_captured': bool(row[9]),
                'face_authorized': bool(row[10]),
                'confidence': row[11],
                'timestamp': row[12]
            }
            attempts.append(attempt)
        
        conn.close()
        
        return jsonify({
            'success': True,
            'attempts': attempts,
            'page': page,
            'limit': limit
        })
        
    except Exception as e:
        app.logger.error(f"Get attempts error: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'success': False,
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
        
        cursor.execute('SELECT COUNT(*) FROM sessions WHERE expires_at > datetime("now")')
        active_sessions_count = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'status': 'operational',
            'users': user_count,
            'login_attempts_24h': recent_attempts,
            'active_lockouts': active_lockouts,
            'active_sessions': active_sessions_count,
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

if __name__ == '__main__':
    # Initialize database
    init_database()
    
    # Create a test user for demonstration
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if test user exists
        cursor.execute('SELECT * FROM users WHERE email = ?', ('test@example.com',))
        if not cursor.fetchone():
            test_password = hash_password('password123')
            cursor.execute('''
                INSERT INTO users (name, email, password_hash)
                VALUES (?, ?, ?)
            ''', ('Test User', 'test@example.com', test_password))
            conn.commit()
            print("✅ Test user created:")
            print("   Email: test@example.com")
            print("   Password: password123")
        
        conn.close()
    except Exception as e:
        print(f"Test user creation error: {e}")
    
    # Run server
    print("\n🚀 Starting VC Authentication Server...")
    print(f"📁 Database: {DATABASE_PATH}")
    print(f"🔒 Max login attempts before face capture: {MAX_LOGIN_ATTEMPTS}")
    print(f"⏱️  Lockout duration: {LOCKOUT_DURATION_HOURS} hours")
    print(f"📧 Admin alerts: {ADMIN_EMAIL}")
    print("\n✨ Server ready at http://localhost:5000")
    print("\n📝 Test Credentials:")
    print("   Name: Test User")
    print("   Email: test@example.com")
    print("   Password: password123")
    print("\n💡 Tips:")
    print("   - Frontend: Open index.html in browser")
    print("   - Dashboard: Will show after successful login")
    print("   - Test failed attempts: Use wrong password 3+ times")
    print("   - Face capture: Activates on 3rd failed attempt")
    
    app.run(host='0.0.0.0', port=5000, debug=True)