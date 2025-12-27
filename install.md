# VC Authentication System - Installation Guide

## 🚀 Quick Start (Recommended)

The fastest way to get started:

```bash
# 1. Make script executable
chmod +x quick_start.sh

# 2. Run it!
./quick_start.sh
```

That's it! The script will:
- ✅ Detect if setup is needed
- ✅ Run full installation if needed
- ✅ Start the server automatically
- ✅ Show you login credentials

---

## 📋 Table of Contents

1. [System Requirements](#system-requirements)
2. [Installation Methods](#installation-methods)
3. [Manual Installation](#manual-installation)
4. [Configuration](#configuration)
5. [User Management](#user-management)
6. [Testing](#testing)
7. [Troubleshooting](#troubleshooting)

---

## 🖥️ System Requirements

### Operating System
- **Linux**: Ubuntu 18.04+, Debian 10+, or similar
- **macOS**: 10.14+
- **Windows**: WSL2 (Windows Subsystem for Linux)

### Software Prerequisites
- Python 3.8 or higher
- SQLite3
- Internet connection (for package downloads)
- At least 1GB free disk space
- Web browser with camera support

### Hardware
- Webcam or camera (for face capture)
- 2GB RAM minimum
- Dual-core processor

---

## 🔧 Installation Methods

### Method 1: Quick Start (Easiest)

Perfect for first-time users:

```bash
chmod +x quick_start.sh
./quick_start.sh
```

### Method 2: Master Setup (Full Control)

For users who want to see each step:

```bash
chmod +x master_setup.sh
./master_setup.sh
```

This will:
1. Install system dependencies
2. Create Python virtual environment
3. Install all Python packages
4. Initialize database
5. Create configuration files
6. Set up startup scripts

### Method 3: Manual Installation

See [Manual Installation](#manual-installation) section below.

---

## 🛠️ Manual Installation

If you prefer to install step-by-step:

### Step 1: Install System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y \
    python3 python3-pip python3-venv python3-dev \
    build-essential cmake pkg-config \
    libopencv-dev libgl1-mesa-glx libglib2.0-0 \
    libsm6 libxext6 libxrender-dev \
    libopenblas-dev liblapack-dev \
    libx11-dev libgtk-3-dev
```

**macOS:**
```bash
# Install Homebrew if not installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python3 cmake pkg-config wget opencv
```

### Step 2: Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel
```

### Step 3: Install Python Packages

```bash
pip install Flask==3.1.2
pip install flask-cors==6.0.2
pip install opencv-python==4.12.0.88
pip install Pillow==12.0.0
pip install numpy==2.2.6
pip install cmake dlib
pip install face-recognition==1.3.0
pip install face_recognition_models==0.3.0
pip install scikit-learn==1.8.0
pip install scipy==1.16.3
```

**Note:** face_recognition installation may take 10-15 minutes.

### Step 4: Create Directory Structure

```bash
mkdir -p database known_faces captured_faces logs
```

### Step 5: Initialize Database

```bash
python3 << 'EOF'
import sqlite3
import hashlib
from pathlib import Path

DATABASE_PATH = 'database/auth.db'
Path('database').mkdir(exist_ok=True)

conn = sqlite3.connect(DATABASE_PATH)
cursor = conn.cursor()

# Create tables
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

# Create test user
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

cursor.execute('SELECT * FROM users WHERE email = ?', ('test@example.com',))
if not cursor.fetchone():
    cursor.execute('''
        INSERT INTO users (name, email, password_hash)
        VALUES (?, ?, ?)
    ''', ('Test User', 'test@example.com', hash_password('password123')))
    print("Test user created")

conn.commit()
conn.close()
print("Database initialized")
EOF
```

### Step 6: Create Configuration File

```bash
cat > .env << 'EOF'
# Flask Configuration
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=change-this-in-production

# Database
DATABASE_PATH=database/auth.db

# Security Settings
MAX_LOGIN_ATTEMPTS=3
LOCKOUT_DURATION_HOURS=5
FACE_MATCH_THRESHOLD=0.6

# Email Settings
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
ADMIN_EMAIL=admin@example.com

# Server Settings
SERVER_HOST=0.0.0.0
SERVER_PORT=5000
EOF
```

### Step 7: Create Start Script

```bash
cat > start.sh << 'EOF'
#!/bin/bash
source venv/bin/activate
echo "🚀 Starting VC Authentication System..."
echo "📡 Backend: http://localhost:5000"
echo "🌐 Frontend: Open index.html in browser"
python app.py
EOF

chmod +x start.sh
```

---

## ⚙️ Configuration

### Email Settings (Optional but Recommended)

Edit `.env` file:

```env
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
ADMIN_EMAIL=admin@example.com
```

**For Gmail:**
1. Enable 2-factor authentication
2. Generate App Password: https://myaccount.google.com/apppasswords
3. Use the 16-character app password

### Security Settings

Adjust in `.env`:

```env
MAX_LOGIN_ATTEMPTS=3           # Face capture after 3 failures
LOCKOUT_DURATION_HOURS=5       # Lock account for 5 hours
FACE_MATCH_THRESHOLD=0.6       # Face similarity threshold
```

---

## 👥 User Management

### Interactive User Management

```bash
chmod +x add_users.sh
./add_users.sh
```

Menu options:
1. Add single user (interactive)
2. List all users
3. View user details
4. Update password
5. Delete user
6. Bulk import from CSV
7. View login attempts
8. View statistics
9. Export users to CSV

### Command Line Usage

```bash
# Add user
./add_users.sh add "John Doe" "john@example.com" "password123"

# List users
./add_users.sh list

# View user
./add_users.sh view john@example.com

# Delete user
./add_users.sh delete john@example.com

# Import from CSV
./add_users.sh import users.csv

# View login attempts
./add_users.sh attempts 50

# View statistics
./add_users.sh stats

# Update password
./add_users.sh password john@example.com
```

### Bulk Import CSV Format

Create `users.csv`:

```csv
name,email,password
John Doe,john@example.com,password123
Jane Smith,jane@example.com,securepass456
Bob Wilson,bob@example.com,mypass789
```

Import:

```bash
./add_users.sh import users.csv
```

---

## 🧪 Testing

### Automated Test Suite

```bash
# Make test script executable
chmod +x test.sh

# Run all tests
./test.sh
```

Tests include:
- ✅ Server health check
- ✅ Database connection
- ✅ User registration
- ✅ Login (success/failure)
- ✅ Session validation
- ✅ Dashboard API
- ✅ Logout functionality

### Manual Testing

1. **Start Server:**
   ```bash
   ./start.sh
   ```

2. **Open Frontend:**
   - Open `index.html` in browser
   - Or use: `python -m http.server 8000`

3. **Test Login:**
   ```
   Name: Test User
   Email: test@example.com
   Password: password123
   ```

4. **Test Failed Attempts:**
   - Enter wrong password 3 times
   - Camera should activate on 3rd attempt
   - Face photo captured

5. **Test Dashboard:**
   - After login, redirected to dashboard
   - See all login attempts
   - View captured faces
   - Check statistics

---

## 🐛 Troubleshooting

### Installation Issues

**Problem: "command not found: python3"**
```bash
# Ubuntu/Debian
sudo apt-get install python3

# macOS
brew install python3
```

**Problem: "pip: command not found"**
```bash
# Ubuntu/Debian
sudo apt-get install python3-pip

# macOS
python3 -m ensurepip
```

**Problem: dlib installation fails**
```bash
# Install build tools
sudo apt-get install build-essential cmake

# Or use pre-built wheel
pip install dlib --no-cache-dir
```

**Problem: face_recognition fails**
```bash
# Install dependencies first
sudo apt-get install libopenblas-dev liblapack-dev

# Then reinstall
pip uninstall face_recognition dlib
pip install --no-cache-dir dlib
pip install face_recognition
```

### Runtime Issues

**Problem: Database locked error**
```bash
# Stop all Python processes
pkill -f "python.*app.py"

# Delete and recreate database
rm database/auth.db
python app.py  # Will recreate database
```

**Problem: Port 5000 already in use**
```bash
# Find and kill process
lsof -ti:5000 | xargs kill -9

# Or change port in app.py
# app.run(host='0.0.0.0', port=5001, debug=True)
```

**Problem: Camera not working**
- Allow camera permissions in browser
- Use HTTPS (or localhost which is exempt)
- Check browser console for errors
- Try different browser (Chrome/Firefox)

**Problem: CORS errors**
- Backend already has CORS enabled
- Check browser console for specific error
- Verify frontend is accessing correct URL
- Clear browser cache

**Problem: Session expired immediately**
- Check system time is correct
- Verify token in localStorage
- Check backend logs for errors
- Try logging out and back in

### Common Questions

**Q: How do I reset admin password?**
```bash
./add_users.sh password admin@example.com
```

**Q: How do I view server logs?**
```bash
tail -f logs/app.log

# Or check terminal output when running ./start.sh
```

**Q: How do I backup the database?**
```bash
cp database/auth.db database/auth_backup_$(date +%Y%m%d).db
```

**Q: How do I restore database?**
```bash
cp database/auth_backup_20250101.db database/auth.db
```

**Q: Can I run on different port?**

Yes, edit last line of `app.py`:
```python
app.run(host='0.0.0.0', port=8000, debug=True)
```

---

## 📚 Additional Resources

- **Frontend Guide:** See `FRONTEND_GUIDE.md`
- **Backend Guide:** See `BACKEND_GUIDE.md`
- **API Documentation:** See `API_DOCUMENTATION.md`
- **Security Guide:** See `SECURITY_GUIDE.md`

---

## 🆘 Getting Help

If issues persist:

1. Check all error messages carefully
2. Review both terminal and browser console
3. Verify all dependencies are installed
4. Test with provided test user first
5. Run automated test suite: `./test.sh`
6. Check file permissions: `chmod +x *.sh`

---

## 📝 Summary of Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `quick_start.sh` | One-command setup & start | `./quick_start.sh` |
| `master_setup.sh` | Full installation | `./master_setup.sh` |
| `start.sh` | Start server | `./start.sh` |
| `stop.sh` | Stop server | `./stop.sh` |
| `test.sh` | Run tests | `./test.sh` |
| `add_users.sh` | Manage users | `./add_users.sh` |

---

**Ready to go! Start with: `./quick_start.sh` 🚀**