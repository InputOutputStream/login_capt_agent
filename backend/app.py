from flask import Flask, request, jsonify
from flask_cors import CORS
import traceback
from datetime import datetime
import hashlib
import sqlite3
from pathlib import Path

app = Flask(__name__)
CORS(app)

# Configuration
DATABASE_PATH = 'database/auth.db'
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 30

# Initialize database
def init_database():
    """Initialize SQLite database with required tables"""
    Path('database').mkdir(exist_ok=True)
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
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
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Lockouts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lockouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            reason TEXT,
            locked_until TIMESTAMP,
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
            severity TEXT DEFAULT 'MEDIUM',
            resolved BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

def get_recent_failed_attempts(email, minutes=60):
    """Get count of recent failed login attempts"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT COUNT(*) FROM login_attempts 
        WHERE email = ? AND success = 0 
        AND timestamp > datetime('now', ?)
    ''', (email, f'-{minutes} minutes'))
    
    count = cursor.fetchone()[0]
    conn.close()
    
    return count

def create_lockout(email, reason):
    """Create a lockout record"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO lockouts (email, reason, locked_until)
        VALUES (?, ?, datetime('now', ?))
    ''', (email, reason, f'+{LOCKOUT_DURATION_MINUTES} minutes'))
    
    # Create admin alert
    cursor.execute('''
        INSERT INTO admin_alerts (alert_type, message, email, severity)
        VALUES (?, ?, ?, ?)
    ''', ('LOCKOUT', f'User {email} locked out: {reason}', email, 'HIGH'))
    
    conn.commit()
    conn.close()

def record_login_attempt(email, success, ip_address=None, user_agent=None):
    """Record a login attempt"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO login_attempts (email, success, ip_address, user_agent)
        VALUES (?, ?, ?, ?)
    ''', (email, success, ip_address, user_agent))
    
    conn.commit()
    conn.close()

# Routes
@app.route('/')
def index():
    """Root endpoint"""
    return jsonify({
        'service': 'Góchat Authentication API',
        'version': '2.0.0',
        'status': 'running'
    })

@app.route('/login', methods=['POST'])
def login():
    """Login endpoint"""
    try:
        data = request.json
        
        name = data.get('name', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        # Get client info
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent', '')
        
        # Validation
        if not name or not email or not password:
            return jsonify({
                'success': False,
                'message': 'All fields are required'
            }), 400
        
        # Check lockout
        if is_locked_out(email):
            return jsonify({
                'success': False,
                'message': f'Account temporarily locked. Try again in {LOCKOUT_DURATION_MINUTES} minutes.',
                'locked': True
            }), 403
        
        # Get user from database
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()
        
        # Verify credentials
        if not user:
            # User doesn't exist
            record_login_attempt(email, False, ip_address, user_agent)
            return jsonify({
                'success': False,
                'message': 'Invalid credentials'
            }), 401
        
        # Check name
        if user['name'].lower() != name.lower():
            record_login_attempt(email, False, ip_address, user_agent)
            return jsonify({
                'success': False,
                'message': 'Invalid credentials'
            }), 401
        
        # Check password
        password_hash = hash_password(password)
        if password_hash != user['password_hash']:
            record_login_attempt(email, False, ip_address, user_agent)
            
            # Check if should lock out
            failed_attempts = get_recent_failed_attempts(email)
            if failed_attempts >= MAX_LOGIN_ATTEMPTS:
                create_lockout(email, f'{failed_attempts} failed login attempts')
                return jsonify({
                    'success': False,
                    'message': f'Too many failed attempts. Account locked for {LOCKOUT_DURATION_MINUTES} minutes.',
                    'locked': True
                }), 403
            
            return jsonify({
                'success': False,
                'message': f'Invalid credentials. Attempt {failed_attempts}/{MAX_LOGIN_ATTEMPTS}'
            }), 401
        
        # Success
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

@app.route('/register', methods=['POST'])
def register():
    """Register new user"""
    try:
        data = request.json
        
        name = data.get('name', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
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
        
        # Insert user
        conn = get_db()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO users (name, email, password_hash)
                VALUES (?, ?, ?)
            ''', (name, email, password_hash))
            
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
        
        conn.close()
        
        return jsonify({
            'status': 'operational',
            'users': user_count,
            'login_attempts_24h': recent_attempts,
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
    print(" Starting Góchat Authentication Server...")
    print(f" Database: {DATABASE_PATH}")
    print(f" Max login attempts: {MAX_LOGIN_ATTEMPTS}")
    print(f"  Lockout duration: {LOCKOUT_DURATION_MINUTES} minutes")
    print("\n Server ready at http://localhost:5000\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)