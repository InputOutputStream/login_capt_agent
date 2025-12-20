document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    const loginBtn = document.getElementById('loginBtn');
    const statusModal = document.getElementById('statusModal');
    const statusIcon = document.getElementById('statusIcon');
    const statusTitle = document.getElementById('statusTitle');
    const statusMessage = document.getElementById('statusMessage');
    const progressBar = document.getElementById('progressBar');


 // API Configuration
    const API_BASE_URL = 'http://localhost:5000';

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

        // Modal functions
        function showModal(type, title, message) {
            const modal = document.getElementById('statusModal');
            const icon = document.getElementById('modalIcon');
            const titleEl = document.getElementById('modalTitle');
            const messageEl = document.getElementById('modalMessage');

            const icons = {
                loading: '⏳',
                success: '✅',
                error: '❌'
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

        // Form submission
        document.getElementById('loginForm').addEventListener('submit', async (e) => {
            e.preventDefault();

            const name = document.getElementById('name').value.trim();
            const email = document.getElementById('email').value.trim();
            const password = document.getElementById('password').value;

            // Validation
            if (!name || !email || !password) {
                showModal('error', 'Error', 'Please fill in all fields');
                setTimeout(hideModal, 3000);
                return;
            }

            try {
                showModal('loading', 'Authenticating', 'Verifying your credentials...');
                updateProgress(30);

                // Call login API
                const result = await api.post('/login', {
                    name: name,
                    email: email,
                    password: password
                });

                updateProgress(100);

                if (result.success) {
                    showModal('success', 'Success!', 'Login successful. Redirecting...');
                    setTimeout(() => {
                        window.location.href = '/dashboard';
                    }, 2000);
                } else {
                    showModal('error', 'Login Failed', result.message || 'Invalid credentials');
                    setTimeout(hideModal, 3000);
                }
            } catch (error) {
                showModal('error', 'Error', error.message);
                setTimeout(hideModal, 3000);
            }
        });

        // Sign up link
        document.getElementById('signupLink').addEventListener('click', (e) => {
            e.preventDefault();
            showModal('loading', 'Coming Soon', 'Sign up functionality will be available soon!');
            setTimeout(hideModal, 3000);
        });

        // Add 3D tilt effect to card
        const card = document.querySelector('.login-card');
        document.addEventListener('mousemove', (e) => {
            const xAxis = (window.innerWidth / 2 - e.pageX) / 50;
            const yAxis = (window.innerHeight / 2 - e.pageY) / 50;
            card.style.transform = `rotateY(${xAxis}deg) rotateX(${yAxis}deg) translateY(-5px)`;
        });

        document.addEventListener('mouseleave', () => {
            card.style.transform = 'rotateY(0deg) rotateX(0deg)';
        });

});