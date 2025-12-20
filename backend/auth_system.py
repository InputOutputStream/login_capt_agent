import sqlite3
import json
import time
import hashlib
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from config import Config

class AuthSystem:
    def __init__(self):
        self.db_path = Config.DATABASE_PATH
        self.max_attempts = Config.MAX_LOGIN_ATTEMPTS
        self.lockout_duration = Config.LOCKOUT_DURATION
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                phone TEXT,
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
                user_id INTEGER,
                email TEXT,
                success BOOLEAN,
                ip_address TEXT,
                user_agent TEXT,
                face_matched BOOLEAN,
                confidence REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Lockouts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lockouts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                email TEXT,
                face_hash TEXT,
                lock_reason TEXT,
                locked_until TIMESTAMP,
                admin_notified BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Admin alerts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_type TEXT,
                message TEXT,
                user_id INTEGER,
                email TEXT,
                severity TEXT,
                resolved BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def hash_password(self, password):
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def hash_face_encoding(self, encoding):
        """Create a hash of face encoding for comparison"""
        if encoding is None:
            return None
        # Convert encoding to bytes and hash
        encoding_bytes = pickle.dumps(encoding)
        return hashlib.md5(encoding_bytes).hexdigest()
    
    def create_user(self, email, phone, password, face_encoding=None):
        """Create a new user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            password_hash = self.hash_password(password)
            
            cursor.execute('''
                INSERT INTO users (email, phone, password_hash, face_encoding)
                VALUES (?, ?, ?, ?)
            ''', (email, phone, password_hash, 
                  pickle.dumps(face_encoding) if face_encoding else None))
            
            user_id = cursor.lastrowid
            conn.commit()
            return user_id
        except sqlite3.IntegrityError:
            return None
        finally:
            conn.close()
    
    def get_user(self, email):
        """Get user by email"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        
        if user and user['face_encoding']:
            user = dict(user)
            user['face_encoding'] = pickle.loads(user['face_encoding'])
        
        conn.close()
        return user
    
    def record_login_attempt(self, email, success, ip_address=None, 
                           user_agent=None, face_matched=None, confidence=None):
        """Record login attempt"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get user_id if exists
        user = self.get_user(email)
        user_id = user['id'] if user else None
        
        cursor.execute('''
            INSERT INTO login_attempts 
            (user_id, email, success, ip_address, user_agent, face_matched, confidence)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, email, success, ip_address, user_agent, 
              face_matched, confidence))
        
        conn.commit()
        conn.close()
        
        # Check if lockout is needed
        if not success:
            self.check_and_lockout(email)
    
    def check_and_lockout(self, email):
        """Check if user should be locked out"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Count recent failed attempts
        cursor.execute('''
            SELECT COUNT(*) FROM login_attempts 
            WHERE email = ? AND success = 0 
            AND timestamp > datetime('now', '-1 hour')
        ''', (email,))
        
        failed_attempts = cursor.fetchone()[0]
        
        if failed_attempts >= self.max_attempts:
            # Create lockout
            locked_until = datetime.now() + self.lockout_duration
            
            cursor.execute('''
                INSERT INTO lockouts (email, lock_reason, locked_until)
                VALUES (?, ?, ?)
            ''', (email, 'Too many failed login attempts', locked_until))
            
            # Create admin alert
            self.create_admin_alert(
                alert_type='LOCKOUT',
                message=f'User {email} locked out due to {failed_attempts} failed attempts',
                email=email,
                severity='HIGH'
            )
            
            conn.commit()
        
        conn.close()
    
    def is_locked_out(self, email, face_hash=None):
        """Check if user is currently locked out"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if face_hash:
            # Check by face hash
            cursor.execute('''
                SELECT * FROM lockouts 
                WHERE face_hash = ? AND locked_until > datetime('now')
                LIMIT 1
            ''', (face_hash,))
        else:
            # Check by email
            cursor.execute('''
                SELECT * FROM lockouts 
                WHERE email = ? AND locked_until > datetime('now')
                LIMIT 1
            ''', (email,))
        
        lockout = cursor.fetchone()
        conn.close()
        
        return lockout is not None
    
    def create_admin_alert(self, alert_type, message, user_id=None, 
                          email=None, severity='MEDIUM'):
        """Create an alert for admin"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO admin_alerts 
            (alert_type, message, user_id, email, severity)
            VALUES (?, ?, ?, ?, ?)
        ''', (alert_type, message, user_id, email, severity))
        
        conn.commit()
        conn.close()
    
    def get_recent_failed_attempts(self, email, hours=1):
        """Get recent failed login attempts"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) FROM login_attempts 
            WHERE email = ? AND success = 0 
            AND timestamp > datetime('now', ?)
        ''', (email, f'-{hours} hours'))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count
    
    def cleanup_old_records(self, days=30):
        """Cleanup old records from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Cleanup old login attempts
        cursor.execute('''
            DELETE FROM login_attempts 
            WHERE timestamp < ?
        ''', (cutoff_date,))
        
        # Cleanup expired lockouts
        cursor.execute('''
            DELETE FROM lockouts 
            WHERE locked_until < datetime('now')
        ''')
        
        conn.commit()
        conn.close()