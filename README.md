# 🔐 VC Authentication System

> **Complete Facial Recognition Security System with Black & White Liquid Ice Glow Theme**

An authentication system featuring facial recognition, real-time location tracking, comprehensive security dashboard, and automated threat detection.

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/flask-3.1.2-red.svg)](https://flask.palletsprojects.com)

---

## Features

### **Modern UI**
- Black & white liquid ice glow theme
- Glassmorphism design with dark mode
- Smooth animations and transitions
- Fully responsive (desktop, tablet, mobile)

### **Security**
- Multi-factor authentication
- Progressive face capture (after 3 failed attempts)
- Automatic account lockout (after 6 failures)
- Real-time threat detection
- Email alerts to administrators

### **Tracking**
- IP address capture
- GPS location tracking (latitude/longitude)
- Browser fingerprinting
- Session management with tokens

### **Dashboard**
- Real-time statistics
- Login attempt history
- Face capture gallery
- Security alerts
- User management

### **Alerts**
- Email notifications for suspicious activity
- Admin dashboard with unresolved alerts
- Captured face images sent to admin
- Lockout notifications

---

## 📋 Prerequisites

### System Requirements
- **RAM**: 2GB minimum, 4GB recommended
- **Storage**: 1GB free disk space
- **Webcam/Camera**: Required for facial recognition
- **Internet**: Required for initial setup

### Software Requirements
- **Python**: 3.8 or higher
- **Database**: SQLite3
- **Web Browser**: Chrome, Firefox, or Edge (latest versions)

---

## 🚀 Installation Guide

### Windows 11 Installation

#### Step 1: Install Python

1. **Download Python**
   - Visit [python.org/downloads](https://www.python.org/downloads/)
   - Download Python 3.11 or later for Windows
   - Run the installer

2. **Configure Python Installation**
   - ✅ **IMPORTANT**: Check "Add Python to PATH"
   - Choose "Customize installation"
   - Select all optional features
   - Click "Install"

3. **Verify Installation**
   ```powershell
   python --version
   pip --version
   ```

#### Step 2: Install Visual Studio Build Tools (Required for face_recognition)

1. **Download VS Build Tools**
   - Visit [visualstudio.microsoft.com/downloads](https://visualstudio.microsoft.com/downloads/)
   - Scroll down to "Tools for Visual Studio"
   - Download "Build Tools for Visual Studio 2022"

2. **Install Required Components**
   - Run the installer
   - Select "Desktop development with C++"
   - Install (this may take 10-20 minutes)

#### Step 3: Install CMake

1. **Download CMake**
   - Visit [cmake.org/download](https://cmake.org/download/)
   - Download the Windows x64 Installer
   - Run installer and select "Add CMake to PATH for all users"

2. **Verify Installation**
   ```powershell
   cmake --version
   ```

#### Step 4: Clone Repository

```powershell
# Using Git (install from git-scm.com if needed)
git clone https://github.com/InputOutputStream/login_capt_agent.git
cd login_capt_agent

# OR download ZIP and extract
# Then navigate to the folder
cd path\to\login_capt_agent
```

#### Step 5: Setup Virtual Environment

```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\activate

# Verify activation (you should see (venv) in prompt)
```

#### Step 6: Install Dependencies

```powershell
# Upgrade pip
python -m pip install --upgrade pip

# Install dlib (may take 5-10 minutes)
pip install dlib

# Install face_recognition
pip install face_recognition

# Install remaining dependencies
pip install -r requirements.txt
```

**If face_recognition fails:**
```powershell
# Try installing from wheel
pip install https://github.com/jloh02/dlib/releases/download/v19.22/dlib-19.22.0-cp311-cp311-win_amd64.whl
pip install face_recognition
```

#### Step 7: Setup Database and Configuration

```powershell
# Create database directory
mkdir database

# Create .env file
copy NUL .env

# Edit .env with Notepad
notepad .env
```

Add to `.env`:
```env
SECRET_KEY=your-secret-key-change-this
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
ADMIN_EMAIL=admin@example.com
```

#### Step 8: Initialize Database

```powershell
python app.py
```

Press `Ctrl+C` after you see "Running on http://127.0.0.1:5000"

#### Step 9: Create Test User

```powershell
python
```

Then in Python:
```python
from app import app, db, User
from werkzeug.security import generate_password_hash

with app.app_context():
    user = User(
        name='Test User',
        email='test@example.com',
        password_hash=generate_password_hash('password123')
    )
    db.session.add(user)
    db.session.commit()
    print("Test user created!")
exit()
```

#### Step 10: Start the Application

```powershell
# Start backend
python app.py

# Open another terminal for frontend
# Navigate to project folder and open index.html in browser
start index.html
```

---

### Ubuntu Installation

#### Step 1: Update System

```bash
sudo apt update && sudo apt upgrade -y
```

#### Step 2: Install Python and Dependencies

```bash
# Install Python 3.11+ and pip
sudo apt install python3.11 python3.11-venv python3-pip -y

# Install build tools
sudo apt install build-essential cmake -y

# Install Python development headers
sudo apt install python3.11-dev -y

# Install additional dependencies for face_recognition
sudo apt install libopenblas-dev liblapack-dev -y
sudo apt install libx11-dev libgtk-3-dev -y
```

#### Step 3: Clone Repository

```bash
# Install git if needed
sudo apt install git -y

# Clone repository
git clone https://github.com/InputOutputStream/login_capt_agent.git
cd login_capt_agent

# OR download and extract ZIP
# wget https://github.com/InputOutputStream/login_capt_agent/archive/refs/heads/main.zip
# unzip main.zip
# cd login_capt_agent-main
```

#### Step 4: Setup Virtual Environment

```bash
# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Verify activation (you should see (venv) in prompt)
```

#### Step 5: Install Python Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install dlib (may take 5-10 minutes to compile)
pip install dlib

# Install face_recognition
pip install face_recognition

# Install remaining dependencies
pip install -r requirements.txt
```

**Alternative if compilation fails:**
```bash
# Use pre-built packages
sudo apt install python3-dlib -y
pip install face_recognition --no-build-isolation
pip install -r requirements.txt
```

#### Step 6: Setup Database and Configuration

```bash
# Create database directory
mkdir -p database

# Create .env file
cat > .env << 'EOF'
SECRET_KEY=your-secret-key-change-this
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
ADMIN_EMAIL=admin@example.com
EOF

# Edit the file
nano .env
# (Press Ctrl+X, then Y, then Enter to save)
```

#### Step 7: Initialize Database

```bash
# Run app briefly to create database
python app.py &
APP_PID=$!
sleep 3
kill $APP_PID
```

#### Step 8: Create Test User

```bash
python3 << 'EOF'
from app import app, db, User
from werkzeug.security import generate_password_hash

with app.app_context():
    user = User(
        name='Test User',
        email='test@example.com',
        password_hash=generate_password_hash('password123')
    )
    db.session.add(user)
    db.session.commit()
    print("Test user created!")
EOF
```

#### Step 9: Make Scripts Executable

```bash
chmod +x scripts/*.sh
chmod +x *.sh
```

#### Step 10: Start the Application

```bash
# Quick start (recommended)
./quick_start.sh

# OR manually
python app.py
```

Then open `index.html` in your browser or:
```bash
# Install a local browser if in GUI environment
xdg-open frontend/index.html

# OR if using SSH, forward port
# ssh -L 5000:localhost:5000 user@server
# Then open http://localhost:5000 on your local machine
```

---

## 🎬 Quick Start (After Installation)

### One-Command Setup (Linux/Mac)

```bash
chmod +x quick_start.sh
./quick_start.sh
```

### Windows PowerShell

```powershell
.\venv\Scripts\activate
python app.py
# Open index.html in browser
```

### Default Login Credentials

```
Name: Test User
Email: test@example.com
Password: password123
```

---

## 🛠️ Automation Scripts

### Available Scripts

1. **quick_start.sh** - One-command setup & start
   ```bash
   ./quick_start.sh
   ```

2. **master_setup.sh** - Full installation process
   ```bash
   ./master_setup.sh
   ```

3. **add_users.sh** - User management tool
   ```bash
   ./add_users.sh
   ```

4. **maintenance.sh** - Database & system maintenance
   ```bash
   ./maintenance.sh
   ```

5. **start.sh** - Start the server
   ```bash
   ./start.sh
   ```

6. **test.sh** - Run automated tests
   ```bash
   ./test.sh
   ```

---

## 📁 Complete System Structure

```
vc-auth-system/
├── Backend
│   ├── app.py                 # Flask server
│   ├── test_system.py         # Automated tests
│   └── database/
│       └── auth.db            # SQLite database
│
├── Frontend
│   ├── index.html             # Login page
│   ├── dashboard.html         # Security dashboard
│   ├── style.css              # Ice glow theme
│   ├── dashboard.css          # Dashboard theme
│   ├── script.js              # Login logic
│   ├── dashboard.js           # Dashboard logic
│   ├── capture.js             # Camera capture
│   └── api.js                 # API client
│
├── Automation Scripts
│   ├── quick_start.sh         # Quick setup
│   ├── master_setup.sh        # Full install
│   ├── add_users.sh           # User management
│   ├── maintenance.sh         # Maintenance
│   ├── start.sh               # Start server
│   └── test.sh                # Run tests
│
└── Documentation
    ├── README.md              # This file
    ├── INSTALLATION_GUIDE.md  # Setup guide
    └── ALL_SCRIPTS_SUMMARY.md # Script reference
```

---

## 🔧 Troubleshooting

### Windows Issues

**1. face_recognition installation fails**
```powershell
# Install Visual Studio Build Tools first
# Then try:
pip install --upgrade pip setuptools wheel
pip install dlib
pip install face_recognition
```

**2. "Python not found" error**
```powershell
# Add Python to PATH manually
# Search "Environment Variables" in Windows
# Add: C:\Users\YourName\AppData\Local\Programs\Python\Python311
# Add: C:\Users\YourName\AppData\Local\Programs\Python\Python311\Scripts
```

**3. Permission denied errors**
```powershell
# Run PowerShell as Administrator
# Right-click PowerShell → "Run as administrator"
```

**4. Port 5000 already in use**
```powershell
# Find and kill process
netstat -ano | findstr :5000
taskkill /PID <process_id> /F
```

### Ubuntu Issues

**1. face_recognition compilation fails**
```bash
# Install all dependencies
sudo apt install build-essential cmake python3-dev
sudo apt install libopenblas-dev liblapack-dev
pip install dlib --no-cache-dir
```

**2. Permission errors**
```bash
# Fix ownership
sudo chown -R $USER:$USER ~/login_capt_agent

# Fix script permissions
chmod +x scripts/*.sh
```

**3. Database locked**
```bash
rm database/auth.db
python app.py
# Will recreate database
```

**4. Port 5000 in use**
```bash
# Find and kill process
sudo lsof -t -i:5000 | xargs sudo kill -9
```

### Common Issues (All Platforms)

**Camera not working**
- Allow camera permissions in browser
- Use HTTPS or localhost
- Try different browser (Chrome recommended)

**Session expired**
- Tokens expire after 24 hours
- Logout and login again
- Clear browser cache

**Dashboard shows no data**
- Check backend is running (`python app.py`)
- Check browser console for errors (F12)
- Verify auth token is valid

---

## 📚 Additional Documentation

- [Installation Guide](install.md) - Detailed setup instructions
- Backend Guide - See comments in `app.py`
- Frontend Guide - See comments in `script.js`

---

## 🔐 Security Notes

### Production Checklist

- [ ] Change SECRET_KEY in .env
- [ ] Configure real email credentials
- [ ] Use HTTPS/SSL certificate
- [ ] Set up proper firewall
- [ ] Regular database backups
- [ ] Monitor logs daily
- [ ] Update dependencies regularly
- [ ] Use strong passwords
- [ ] Restrict admin access

---

## 📝 License

MIT License - see LICENSE file

---

## 🆘 Support

### Quick Help

```bash
# Reset everything (Linux/Mac)
rm -rf database venv
./quick_start.sh

# Windows
Remove-Item -Recurse -Force database, venv
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

### Get Help

- Check [Troubleshooting](#troubleshooting) section
- Review installation steps carefully
- Check system requirements
- Open an issue on GitHub

---

## 🎯 Next Steps After Installation

1. **Test the System**
   ```bash
   ./test.sh  # Linux/Mac
   python test_system.py  # Windows
   ```

2. **Add Real Users**
   ```bash
   ./add_users.sh  # Linux/Mac
   # Follow prompts
   ```

3. **Configure Email**
   - Get Gmail App Password: https://myaccount.google.com/apppasswords
   - Update .env file with credentials

4. **Customize Settings**
   - Edit `app.py` for security thresholds
   - Modify `style.css` for theme changes
   - Adjust lockout duration

5. **Deploy to Production**
   - Use Gunicorn or uWSGI
   - Set up Nginx reverse proxy
   - Enable SSL/TLS
   - Configure firewall rules

---
