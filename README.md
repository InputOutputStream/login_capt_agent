# 🔐 VC Authentication System

> **Complete Facial Recognition Security System with Black & White Liquid Ice Glow Theme**

A production-ready authentication system featuring facial recognition, real-time location tracking, comprehensive security dashboard, and automated threat detection.

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

## 🎬 Quick Start

### One-Command Setup

```bash
chmod +x quick_start.sh
./quick_start.sh
```

That's it! The system will:
1. Install all dependencies
2. Set up the database
3. Create test user
4. Start the server
5. Open ready to use

### Default Login

```
Name: Test User
Email: test@example.com
Password: password123
```

---


### 🛠️ **6 Automation Scripts**

1. **quick_start.sh** - One-command setup & start
2. **master_setup.sh** - Full installation process
3. **add_users.sh** - User management tool
4. **maintenance.sh** - Database & system maintenance
5. **start.sh** - Start the server
6. **test.sh** - Run automated tests

### **Complete System**

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

## Installation

### Prerequisites

- Python 3.8+
- SQLite3
- Webcam/camera
- 2GB RAM minimum
- 1GB free disk space

### Method 1: Quick Start (Recommended)

```bash
./quick_start.sh
```

### Method 2: Step-by-Step

```bash
# 1. Run master setup
./master_setup.sh

# 2. Start server
./start.sh

# 3. Open browser
# Open index.html
```

### Method 3: Manual

See [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md) for detailed instructions.

---

## Usage

### Starting the System

```bash
./start.sh
```

Server starts at: `http://localhost:5000`
Frontend: Open `index.html` in browser

### Adding Users

**Interactive:**
```bash
./add_users.sh
```

**Command Line:**
```bash
./add_users.sh add "John Doe" "john@example.com" "password123"
```

**Bulk Import:**
```bash
# Create users.csv
cat > users.csv << EOF
name,email,password
Alice,alice@example.com,pass1
Bob,bob@example.com,pass2
EOF

# Import
./add_users.sh import users.csv
```

### Maintenance

```bash
# Interactive maintenance menu
./maintenance.sh

# Or command line
./maintenance.sh backup     # Backup database
./maintenance.sh clean       # Clean old records
./maintenance.sh stats       # View statistics
./maintenance.sh health      # Health check
```

### Testing

```bash
./test.sh
```

---

## How It Works

### Login Flow

```
1. User enters credentials
   ↓
2. Backend validates
   ↓
3a. Success → Dashboard
   ↓
3b. Failed → Counter++
   ↓
4. If attempts ≥ 3 → Activate camera
   ↓
5. Capture face photo
   ↓
6. Store with attempt data
   ↓
7. If attempts ≥ 6 → Lock account
   ↓
8. Email admin with faces
```

### Security Workflow

```
Attempt 1-2:  Password check only
Attempt 3:    Camera activates + Photo capture
Attempt 3:    Warning email to admin
Attempt 4-5:  Continued photo capture
Attempt 6:    Account locked for 5 hours
Attempt 6:    Lockout email with all photos
```

### Data Captured

For each login attempt:
- User name and email
- Success/failure status
- Client IP address
- Browser user agent
- GPS coordinates (lat/lng)
- Timestamp
- Face photo (on 3+ failures)
- Face recognition confidence

---

## Design System

### Color Palette

```css
Background:     #0a0a0a (Deep black)
Cards:          rgba(20, 20, 20, 0.85)
Primary Text:   #ffffff (White)
Secondary Text: #b0b0b0 (Light gray)
Borders:        rgba(255, 255, 255, 0.1-0.3)
Success:        #81c784 (Light green)
Error:          #e57373 (Light red)
Warning:        #ffb74d (Orange)
```

### Visual Effects

-  Ice glow borders and shadows
-  Glassmorphism with backdrop blur
-  Liquid blob animations
-  Subtle grid overlay
-  Smooth hover transitions

---

## 📡 API Reference

### Authentication

**POST /login**
```json
{
  "name": "Test User",
  "email": "test@example.com",
  "password": "password123",
  "latitude": 37.7749,
  "longitude": -122.4194,
  "face_image": "data:image/jpeg;base64,..."
}
```

**POST /logout**
```
Headers: Authorization: Bearer <token>
```

**GET /validate-session**
```
Headers: Authorization: Bearer <token>
```

### Dashboard

**GET /admin/login-attempts**
```
Headers: Authorization: Bearer <token>
Query: ?page=1&limit=100
```

**GET /admin/alerts**
```
Returns unresolved security alerts
```

### System

**GET /health**
```
System health check
```

**GET /status**
```
System statistics
```

---

## 🔧 Configuration

### Email Settings

Edit `.env`:

```env
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
ADMIN_EMAIL=admin@example.com
```

For Gmail: [Generate App Password](https://myaccount.google.com/apppasswords)

### Security Settings

```env
MAX_LOGIN_ATTEMPTS=3           # Face capture after 3
LOCKOUT_DURATION_HOURS=5       # Lock for 5 hours
FACE_MATCH_THRESHOLD=0.6       # Face similarity
```

---

## Scripts Reference

| Script | Purpose | Usage |
|--------|---------|-------|
| `quick_start.sh` | One-command setup | `./quick_start.sh` |
| `master_setup.sh` | Full installation | `./master_setup.sh` |
| `add_users.sh` | Manage users | `./add_users.sh` |
| `maintenance.sh` | System maintenance | `./maintenance.sh` |
| `start.sh` | Start server | `./start.sh` |
| `stop.sh` | Stop server | `./stop.sh` |
| `test.sh` | Run tests | `./test.sh` |

---

## 📊 Dashboard Features

### Statistics Cards
- Total login attempts
- Successful logins
- Failed attempts
- Faces captured

### Login Attempts Table
- Timestamp (relative time)
- User name and email
- Success/Failed status
- IP address
- GPS location
- Face thumbnail (click to enlarge)
- View details button

### Features
- Auto-refresh every 30 seconds
- Face image modal viewer
- Logout button
- Responsive design

---

## 🧪 Testing

### Automated Tests

```bash
./test.sh
```

Tests:
-  Server health
-  Database connection
-  User registration
-  Login/logout
-  Session management
-  Dashboard API

### Manual Testing

1. **Successful Login**
   - Use test@example.com / password123
   - Should redirect to dashboard

2. **Failed Login + Face Capture**
   - Enter wrong password 3 times
   - Camera activates on 3rd attempt
   - Photo captured and displayed

3. **Account Lockout**
   - Continue with 6 failed attempts
   - Account locked
   - Admin receives email

---

## 🐛 Troubleshooting

### Installation Issues

**Face recognition fails to install:**
```bash
sudo apt-get install build-essential cmake
pip install --no-cache-dir dlib
pip install face_recognition
```

**Database locked:**
```bash
rm database/auth.db
python app.py
```

**Port 5000 in use:**
```bash
lsof -ti:5000 | xargs kill -9
```

### Runtime Issues

**Camera not working:**
- Allow camera permissions
- Use HTTPS or localhost
- Try different browser

**Session expired:**
- Tokens expire after 24 hours
- Logout and login again

**Dashboard shows no data:**
- Check backend is running
- Check browser console
- Verify auth token

---

## 📚 Documentation

- [Installation Guide](install.md)
- Backend Guide (in app.py)
- Frontend Guide (in script.js)

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

### Best Practices

1. **Passwords**: Min 8 chars, mixed case, numbers, symbols
2. **Backups**: Daily automated backups
3. **Monitoring**: Check logs and alerts daily
4. **Updates**: Keep system and packages updated
5. **Testing**: Test after changes

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create feature branch
3. Make changes
4. Test thoroughly
5. Submit pull request

---

## 📝 License

MIT License - see LICENSE file

---

## 🆘 Support

### Quick Help

```bash
# Reset everything
rm -rf database venv
./quick_start.sh

# View logs
tail -f logs/app.log

# Check health
./maintenance.sh health

# Backup database
./maintenance.sh backup
```

### Common Issues

1. **Can't install?** Check prerequisites
2. **Server won't start?** Check port 5000
3. **Camera not working?** Allow permissions
4. **Database errors?** Reset database

---

## 🎯 Roadmap

- [ ] Multi-language support
- [ ] 2FA with TOTP
- [ ] Mobile app
- [ ] Advanced analytics
- [ ] Role-based access control
- [ ] API rate limiting
- [ ] Redis session storage
- [ ] Docker deployment


