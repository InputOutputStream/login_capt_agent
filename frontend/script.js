document.addEventListener('DOMContentLoaded', function() {
    // API Configuration
    const API_BASE_URL = 'http://localhost:5000';

    // Check if already logged in
    // checkExistingSession();

    // API helper functions
    const api = {
        async post(endpoint, data) {
            try {
                const response = await fetch(`${API_BASE_URL}${endpoint}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                });
                return await response.json();
            } catch (error) {
                throw new Error('Network error: ' + error.message);
            }
        },

        async get(endpoint) {
            try {
                const response = await fetch(`${API_BASE_URL}${endpoint}`);
                return await response.json();
            } catch (error) {
                throw new Error('Network error: ' + error.message);
            }
        }
    };

    // Check if user is already logged in
    async function checkExistingSession() {
        const token = localStorage.getItem('auth_token');
        if (token) {
            // User might already be logged in, redirect to dashboard
            window.location.href = '/dashboard.html';
        }
    }

    // Modal functions
    function showModal(type, title, message) {
        const modal = document.getElementById('statusModal');
        const icon = document.getElementById('modalIcon');
        const titleEl = document.getElementById('modalTitle');
        const messageEl = document.getElementById('modalMessage');

        const icons = {
            loading: '⏳',
            success: '✅',
            error: '❌',
            warning: '⚠️',
            camera: '📷'
        };

        icon.textContent = icons[type] || '⏳';
        icon.className = `modal-icon ${type}`;
        titleEl.textContent = title;
        messageEl.textContent = message;

        modal.classList.add('show');
    }

    function hideModal() {
        const modal = document.getElementById('statusModal');
        modal.classList.remove('show');
        document.getElementById('progressFill').style.width = '0%';
    }

    function updateProgress(percent) {
        document.getElementById('progressFill').style.width = percent + '%';
    }

    // Face capture function
    async function captureFaceForSecurity(email) {
        try {
            showModal('camera', 'Face Verification', 'Capturing image for security check...');
            updateProgress(30);

            // Check if security camera is available
            if (!window.securityCamera) {
                throw new Error('Security camera system not initialized');
            }

            // Capture face
            const result = await window.securityCamera.captureFaceForVerification(email);
            updateProgress(70);

            if (!result.success) {
                throw new Error(result.error || 'Failed to capture face');
            }

            updateProgress(100);
            return result;
        } catch (error) {
            console.error('Face capture error:', error);
            throw error;
        }
    }

    // Get user's location
    async function getUserLocation() {
        return new Promise((resolve) => {
            if (!navigator.geolocation) {
                resolve({ latitude: null, longitude: null });
                return;
            }

            navigator.geolocation.getCurrentPosition(
                (position) => {
                    resolve({
                        latitude: position.coords.latitude,
                        longitude: position.coords.longitude
                    });
                },
                (error) => {
                    console.warn('Geolocation error:', error);
                    resolve({ latitude: null, longitude: null });
                },
                { timeout: 5000 }
            );
        });
    }

    // Get user's IP address (backend will capture this, but we can try client-side too)
    async function getUserIP() {
        try {
            const response = await fetch('https://api.ipify.org?format=json');
            const data = await response.json();
            return data.ip;
        } catch (error) {
            console.warn('Failed to get IP:', error);
            return null;
        }
    }

    // Form submission with facial recognition
    document.getElementById('loginForm').addEventListener('submit', async (e) => {
        e.preventDefault();

        const name = document.getElementById('name').value.trim();
        const email = document.getElementById('email').value.trim().toLowerCase();
        const password = document.getElementById('password').value;

        // Validation
        if (!name || !email || !password) {
            showModal('error', 'Error', 'Please fill in all fields');
            setTimeout(hideModal, 3000);
            return;
        }

        try {
            showModal('loading', 'Authenticating', 'Verifying your credentials...');
            updateProgress(10);

            // Get user location and IP
            const location = await getUserLocation();
            const ipAddress = await getUserIP();
            updateProgress(20);

            // First, check if we need to capture face
            let faceImage = null;
            let requireFace = false;

            // Check local storage for failed attempts
            const attemptKey = `failed_attempts_${email}`;
            let failedAttempts = parseInt(localStorage.getItem(attemptKey)) || 0;

            // If 3 or more failed attempts, capture face
            if (failedAttempts >= 3) {
                requireFace = true;
                try {
                    const faceResult = await captureFaceForSecurity(email);
                    faceImage = faceResult.image;
                } catch (error) {
                    showModal('error', 'Camera Required', 
                        'Face verification required but camera unavailable. Please enable camera access.');
                    setTimeout(hideModal, 5000);
                    return;
                }
            }

            // Call login API
            const loginData = {
                name: name,
                email: email,
                password: password,
                latitude: location.latitude,
                longitude: location.longitude,
                ip_address: ipAddress
            };

            // Add face image if captured
            if (faceImage) {
                loginData.face_image = faceImage;
            }

            const result = await api.post('/login', loginData);
            updateProgress(80);

            if (result.success) {
                // Reset failed attempts
                localStorage.removeItem(attemptKey);
                
                // Store authentication token and user info
                if (result.token) {
                    localStorage.setItem('auth_token', result.token);
                }
                localStorage.setItem('user_email', email);
                localStorage.setItem('user_name', name);
                
                updateProgress(100);

                showModal('success', 'Success!', 'Login successful. Redirecting to dashboard...');
                setTimeout(() => {
                    window.location.href = '/dashboard.html';
                }, 1500);
            } else {
                // Increment failed attempts
                failedAttempts++;
                localStorage.setItem(attemptKey, failedAttempts.toString());

                updateProgress(100);

                if (result.locked) {
                    showModal('error', 'Account Locked', 
                        'Too many failed attempts. Account locked for 5 hours. Admin has been notified.');
                    setTimeout(hideModal, 5000);
                } else if (result.require_face) {
                    showModal('warning', 'Security Check Required', 
                        `Failed attempt ${failedAttempts}/3. Camera verification will be required on next attempt.`);
                    setTimeout(hideModal, 4000);
                } else {
                    const attemptsRemaining = 3 - failedAttempts;
                    showModal('error', 'Login Failed', 
                        result.message || `Invalid credentials. ${attemptsRemaining} attempts remaining before face capture.`);
                    setTimeout(hideModal, 3000);
                }
            }
        } catch (error) {
            updateProgress(100);
            showModal('error', 'Connection Error', error.message || 'Unable to connect to server');
            setTimeout(hideModal, 3000);
        }
    });

    // // Sign up link
    // document.getElementById('signupLink').addEventListener('click', (e) => {
    //     e.preventDefault();
    //     showModal('loading', 'Registration', 'Redirecting to registration...');
        
    //     // Simulate registration page
    //     setTimeout(() => {
    //         window.location.href = '/register.html';
    //     }, 1500);
    // });

    // Add 3D tilt effect to card
    const card = document.querySelector('.login-card');
    if (card) {
        document.addEventListener('mousemove', (e) => {
            const xAxis = (window.innerWidth / 2 - e.pageX) / 50;
            const yAxis = (window.innerHeight / 2 - e.pageY) / 50;
            card.style.transform = `rotateY(${xAxis}deg) rotateX(${yAxis}deg) translateY(-5px)`;
        });

        document.addEventListener('mouseleave', () => {
            card.style.transform = 'rotateY(0deg) rotateX(0deg)';
        });
    }

    // Initialize security camera system
    console.log('Security system initialized');
    if (!window.securityCamera) {
        console.warn('Security camera system not loaded');
    }
});