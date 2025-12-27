#!/bin/bash

################################################################################
# VC Authentication System - Master Setup Script
# This script automates the complete installation and setup process
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
PYTHON_VERSION="3.8"
PROJECT_ROOT="$(pwd)"
BACKEND_DIR="$PROJECT_ROOT"
FRONTEND_DIR="$PROJECT_ROOT"
DATABASE_DIR="$PROJECT_ROOT/database"
VENV_DIR="$PROJECT_ROOT/venv"

# Functions
print_banner() {
    clear
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║        VC AUTHENTICATION SYSTEM - MASTER SETUP               ║"
    echo "║                                                              ║"
    echo "║     Complete Facial Recognition & Security System           ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}\n"
}

print_step() {
    echo -e "\n${BLUE}▶ $1${NC}"
    echo -e "${BLUE}$( printf '%.0s─' {1..70} )${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ $1${NC}"
}

# Check if running as root
check_root() {
    if [ "$EUID" -eq 0 ]; then 
        print_warning "Please do not run this script as root"
        echo "Run as regular user. Sudo will be requested when needed."
        exit 1
    fi
}

# Detect OS
detect_os() {
    print_step "Detecting Operating System"
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
        if [ -f /etc/os-release ]; then
            . /etc/os-release
            DISTRO=$ID
            print_success "Detected: $PRETTY_NAME"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        print_success "Detected: macOS"
    else
        OS="unknown"
        print_error "Unsupported operating system: $OSTYPE"
        exit 1
    fi
}

# Install system dependencies
install_system_dependencies() {
    print_step "Installing System Dependencies"
    
    if [ "$OS" == "linux" ]; then
        print_info "Updating package lists..."
        sudo apt-get update -y
        
        print_info "Installing Python and development tools..."
        sudo apt-get install -y \
            python3 \
            python3-pip \
            python3-venv \
            python3-dev \
            build-essential \
            cmake \
            pkg-config \
            wget \
            curl \
            git
        
        print_info "Installing OpenCV and imaging dependencies..."
        sudo apt-get install -y \
            libopencv-dev \
            libgl1-mesa-glx \
            libglib2.0-0 \
            libsm6 \
            libxext6 \
            libxrender-dev \
            libgomp1 \
            libgstreamer1.0-0 \
            gstreamer1.0-plugins-base \
            gstreamer1.0-plugins-good
        
        print_info "Installing dlib dependencies..."
        sudo apt-get install -y \
            libopenblas-dev \
            liblapack-dev \
            libx11-dev \
            libgtk-3-dev
        
        print_success "System dependencies installed"
        
    elif [ "$OS" == "macos" ]; then
        # Check for Homebrew
        if ! command -v brew &> /dev/null; then
            print_info "Installing Homebrew..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        fi
        
        print_info "Installing dependencies via Homebrew..."
        brew install python3 cmake pkg-config wget
        brew install opencv
        
        print_success "System dependencies installed"
    fi
}

# Create directory structure
create_directories() {
    print_step "Creating Directory Structure"
    
    mkdir -p "$DATABASE_DIR"
    mkdir -p "$PROJECT_ROOT/known_faces"
    mkdir -p "$PROJECT_ROOT/captured_faces"
    mkdir -p "$PROJECT_ROOT/logs"
    
    print_success "Directories created:"
    echo "   • database/"
    echo "   • known_faces/"
    echo "   • captured_faces/"
    echo "   • logs/"
}

# Create Python virtual environment
create_venv() {
    print_step "Creating Python Virtual Environment"
    
    if [ -d "$VENV_DIR" ]; then
        print_warning "Virtual environment already exists. Removing..."
        rm -rf "$VENV_DIR"
    fi
    
    python3 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    
    print_info "Upgrading pip..."
    pip install --upgrade pip setuptools wheel
    
    print_success "Virtual environment created at: $VENV_DIR"
}

# Install Python dependencies
install_python_dependencies() {
    print_step "Installing Python Dependencies"
    
    source "$VENV_DIR/bin/activate"
    
    print_info "Installing core packages..."
    pip install Flask==3.1.2
    pip install flask-cors==6.0.2
    
    print_info "Installing imaging and computer vision packages..."
    pip install opencv-python==4.12.0.88
    pip install Pillow==12.0.0
    pip install numpy==2.2.6
    
    print_info "Installing face recognition (this may take a while)..."
    pip install cmake
    pip install dlib
    pip install face-recognition==1.3.0
    pip install face_recognition_models==0.3.0
    
    print_info "Installing additional packages..."
    pip install scikit-learn==1.8.0
    pip install scipy==1.16.3
    
    # Save requirements
    pip freeze > requirements.txt
    
    print_success "Python dependencies installed"
}

# Initialize database
initialize_database() {
    print_step "Initializing Database"
    
    source "$VENV_DIR/bin/activate"
    
    # Run Python script to initialize database
    python3 << 'EOF'
import sqlite3
import hashlib
from pathlib import Path

DATABASE_PATH = 'database/auth.db'
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

# Sessions table
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
    print("✓ Test user created: test@example.com / password123")

conn.commit()
conn.close()
print("✓ Database initialized successfully")
EOF
    
    print_success "Database initialized at: $DATABASE_DIR/auth.db"
}

# Create configuration file
create_config() {
    print_step "Creating Configuration Files"
    
    # Create .env file
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

# Email Settings (Update these!)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
ADMIN_EMAIL=admin@example.com

# Server Settings
SERVER_HOST=0.0.0.0
SERVER_PORT=5000
EOF
    
    print_success "Configuration file created: .env"
    print_warning "⚠️  Remember to update email settings in .env file!"
}

# Create startup scripts
create_startup_scripts() {
    print_step "Creating Startup Scripts"
    
    # Create start.sh
    cat > start.sh << 'EOF'
#!/bin/bash

# Activate virtual environment
source venv/bin/activate

# Start Flask server
echo " Starting VC Authentication System..."
echo " Backend running at http://localhost:5000"
echo " Open frontend/index.html in your browser"
echo ""
python app.py
EOF
    chmod +x start.sh
    
    # Create stop.sh
    cat > stop.sh << 'EOF'
#!/bin/bash

echo "Stopping VC Authentication System..."
pkill -f "python.*app.py"
echo "✓ Server stopped"
EOF
    chmod +x stop.sh
    
    # Create test.sh
    cat > test.sh << 'EOF'
#!/bin/bash

source venv/bin/activate
python test_system.py
EOF
    chmod +x test.sh
    
    print_success "Startup scripts created:"
    echo "   • start.sh - Start the server"
    echo "   • stop.sh - Stop the server"
    echo "   • test.sh - Run test suite"
}

# Create README
create_readme() {
    print_step "Creating Documentation"
    
    cat > SETUP_COMPLETE.md << 'EOF'
# VC Authentication System - Setup Complete! 🎉

## 📋 What Was Installed

; System dependencies (Python, OpenCV, CMake)
; Python virtual environment
; All Python packages (Flask, face_recognition, etc.)
; Database initialized with test user
; Directory structure created
; Configuration files created
; Startup scripts created

## Quick Start

### Start the System

```bash
./start.sh
```

Then open `index.html` in your browser.

### Test Credentials

```
Name: Test User
Email: test@example.com
Password: password123
```

## Project Structure

```
vc-auth-system/
├── app.py                 # Main backend server
├── database/
│   └── auth.db           # SQLite database
├── known_faces/          # Registered face images
├── captured_faces/       # Security captures
├── logs/                 # System logs
├── venv/                 # Python virtual environment
├── index.html           # Login page
├── dashboard.html       # Security dashboard
└── *.js, *.css         # Frontend files
```

##  Common Commands

```bash
# Start server
./start.sh

# Stop server
./stop.sh

# Run tests
./test.sh

# Add users
./add_users.sh

# View logs
tail -f logs/app.log
```

## 📧 Email Configuration

Edit `.env` file and update:

```env
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
ADMIN_EMAIL=admin@example.com
```

For Gmail, use an [App Password](https://myaccount.google.com/apppasswords).

## 🧪 Testing the System

1. **Login Test**: Use test credentials above
2. **Failed Attempts**: Try wrong password 3 times to trigger face capture
3. **Dashboard**: View all login attempts with locations and faces
4. **Logout**: Test session management

##  Troubleshooting

**Camera not working?**
- Allow camera permissions in browser
- Use HTTPS or localhost

**Database errors?**
```bash
rm database/auth.db
python app.py  # Re-initializes database
```

**Port 5000 in use?**
- Change port in app.py or kill existing process

## 📚 Documentation

- Frontend: See FRONTEND_GUIDE.md
- Backend: See BACKEND_GUIDE.md
- API: See API_DOCUMENTATION.md

## 🔐 Security Notes

- Change SECRET_KEY in production
- Use HTTPS in production
- Set up proper firewall rules
- Regular database backups
- Monitor logs for suspicious activity

---

**System is ready! Start with: `./start.sh`**
EOF
    
    print_success "Documentation created: SETUP_COMPLETE.md"
}

# Run system tests
run_tests() {
    print_step "Running System Tests"
    
    source "$VENV_DIR/bin/activate"
    
    print_info "Testing Python imports..."
    python3 << 'EOF'
try:
    import flask
    import cv2
    import face_recognition
    import numpy
    import PIL
    print("✓ All imports successful")
except ImportError as e:
    print(f"✗ Import error: {e}")
    exit(1)
EOF
    
    print_info "Testing database connection..."
    python3 << 'EOF'
import sqlite3
try:
    conn = sqlite3.connect('database/auth.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users')
    count = cursor.fetchone()[0]
    print(f"✓ Database connected. Users: {count}")
    conn.close()
except Exception as e:
    print(f"✗ Database error: {e}")
    exit(1)
EOF
    
    print_success "All tests passed!"
}

# Print completion message
print_completion() {
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                              ║${NC}"
    echo -e "${GREEN}║           ✓ INSTALLATION COMPLETE!                          ║${NC}"
    echo -e "${GREEN}║                                                              ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${CYAN} VC Authentication System is ready!${NC}"
    echo ""
    echo -e "${YELLOW}📝 Next Steps:${NC}"
    echo ""
    echo -e "   1️⃣  Update email settings in ${BLUE}.env${NC} file"
    echo -e "   2️⃣  Start the server:"
    echo -e "      ${GREEN}./start.sh${NC}"
    echo ""
    echo -e "   3️⃣  Open ${BLUE}index.html${NC} in your browser"
    echo ""
    echo -e "   4️⃣  Login with test credentials:"
    echo -e "      ${CYAN}Email:${NC} test@example.com"
    echo -e "      ${CYAN}Password:${NC} password123"
    echo ""
    echo -e "${YELLOW}📚 Documentation:${NC} See ${BLUE}SETUP_COMPLETE.md${NC}"
    echo ""
    echo -e "${YELLOW}🧪 Run tests:${NC} ${GREEN}./test.sh${NC}"
    echo -e "${YELLOW}👥 Add users:${NC} ${GREEN}./add_users.sh${NC}"
    echo ""
    echo -e "${GREEN}Happy coding! 🚀${NC}"
    echo ""
}

# Main installation process
main() {
    print_banner
    
    # Pre-flight checks
    check_root
    detect_os
    
    # Confirmation
    echo -e "${YELLOW}This script will:${NC}"
    echo "  • Install system dependencies"
    echo "  • Create Python virtual environment"
    echo "  • Install all Python packages"
    echo "  • Initialize database"
    echo "  • Create configuration files"
    echo "  • Set up startup scripts"
    echo ""
    read -p "Continue? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_warning "Installation cancelled"
        exit 0
    fi
    
    # Installation steps
    install_system_dependencies
    create_directories
    create_venv
    install_python_dependencies
    initialize_database
    create_config
    create_startup_scripts
    create_readme
    run_tests
    
    # Complete
    print_completion
}

# Run main function
main "$@"