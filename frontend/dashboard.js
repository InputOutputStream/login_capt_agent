// dashboard.js

document.addEventListener('DOMContentLoaded', function() {
    const API_BASE_URL = 'http://localhost:5000';
    let loginAttemptsData = [];
    let currentUser = null;

    // Initialize dashboard
    init();

    async function init() {
        try {
            showLoading();
            await checkAuthentication();
            await loadUserInfo();
            await loadLoginAttempts();
            hideLoading();
        } catch (error) {
            console.error('Initialization error:', error);
            hideLoading();
            redirectToLogin();
        }
    }

    // Check if user is authenticated
    async function checkAuthentication() {
        const token = localStorage.getItem('auth_token');
        const userEmail = localStorage.getItem('user_email');
        
        if (!token || !userEmail) {
            redirectToLogin();
            return;
        }

        try {
            const response = await fetch(`${API_BASE_URL}/validate-session`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error('Session invalid');
            }

            const data = await response.json();
            if (!data.success) {
                throw new Error('Session expired');
            }
        } catch (error) {
            console.error('Auth check failed:', error);
            redirectToLogin();
        }
    }

    // Load user information
    async function loadUserInfo() {
        const userName = localStorage.getItem('user_name') || 'User';
        const userEmail = localStorage.getItem('user_email') || '';
        
        document.getElementById('userName').textContent = userName;
        
        currentUser = {
            name: userName,
            email: userEmail
        };
    }

    // Load login attempts from backend
    async function loadLoginAttempts() {
        try {
            const token = localStorage.getItem('auth_token');
            const response = await fetch(`${API_BASE_URL}/admin/login-attempts`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error('Failed to fetch login attempts');
            }

            const data = await response.json();
            loginAttemptsData = data.attempts || [];
            
            updateStats();
            renderLoginAttempts();
        } catch (error) {
            console.error('Error loading login attempts:', error);
            // Use mock data for testing if backend is not available
            useMockData();
        }
    }

    // Use mock data for testing (remove this in production)
    function useMockData() {
        loginAttemptsData = [
            {
                id: 1,
                timestamp: new Date().toISOString(),
                name: 'John Doe',
                email: 'john@example.com',
                success: true,
                ip_address: '192.168.1.100',
                latitude: 37.7749,
                longitude: -122.4194,
                face_image: null
            },
            {
                id: 2,
                timestamp: new Date(Date.now() - 3600000).toISOString(),
                name: 'Jane Smith',
                email: 'jane@example.com',
                success: false,
                ip_address: '192.168.1.101',
                latitude: 34.0522,
                longitude: -118.2437,
                face_image: 'data:image/jpeg;base64,/9j/4AAQSkZJRg...' // Mock base64
            },
            {
                id: 3,
                timestamp: new Date(Date.now() - 7200000).toISOString(),
                name: 'Bob Wilson',
                email: 'bob@example.com',
                success: false,
                ip_address: '192.168.1.102',
                latitude: 40.7128,
                longitude: -74.0060,
                face_image: 'data:image/jpeg;base64,/9j/4AAQSkZJRg...'
            }
        ];
        
        updateStats();
        renderLoginAttempts();
    }

    // Update statistics
    function updateStats() {
        const total = loginAttemptsData.length;
        const successful = loginAttemptsData.filter(a => a.success).length;
        const failed = total - successful;
        const faceCaptured = loginAttemptsData.filter(a => a.face_image).length;

        document.getElementById('totalAttempts').textContent = total;
        document.getElementById('successAttempts').textContent = successful;
        document.getElementById('failedAttempts').textContent = failed;
        document.getElementById('capturedFaces').textContent = faceCaptured;
    }

    // Render login attempts table
    function renderLoginAttempts() {
        const tbody = document.getElementById('attemptsTableBody');
        tbody.innerHTML = '';

        if (loginAttemptsData.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" style="text-align: center; padding: 40px; color: #808080;">
                        No login attempts found
                    </td>
                </tr>
            `;
            return;
        }

        // Sort by timestamp (newest first)
        const sortedAttempts = [...loginAttemptsData].sort((a, b) => 
            new Date(b.timestamp) - new Date(a.timestamp)
        );

        sortedAttempts.forEach(attempt => {
            const row = createAttemptRow(attempt);
            tbody.appendChild(row);
        });
    }

    // Create table row for login attempt
    function createAttemptRow(attempt) {
        const tr = document.createElement('tr');
        
        const timestamp = formatTimestamp(attempt.timestamp);
        const statusClass = attempt.success ? 'status-success' : 'status-failed';
        const statusText = attempt.success ? 'Success' : 'Failed';
        const location = formatLocation(attempt.latitude, attempt.longitude);
        
        tr.innerHTML = `
            <td>${timestamp}</td>
            <td>${escapeHtml(attempt.name || 'N/A')}</td>
            <td>${escapeHtml(attempt.email || 'N/A')}</td>
            <td><span class="status-badge ${statusClass}">${statusText}</span></td>
            <td>${escapeHtml(attempt.ip_address || 'N/A')}</td>
            <td>${location}</td>
            <td>${attempt.face_image ? 
                `<img src="${attempt.face_image}" class="face-thumbnail" data-id="${attempt.id}">` : 
                '<span class="no-face">No capture</span>'
            }</td>
            <td><button class="view-btn" data-id="${attempt.id}">View Details</button></td>
        `;
        
        // Add event listeners
        const faceImg = tr.querySelector('.face-thumbnail');
        if (faceImg) {
            faceImg.addEventListener('click', () => showFaceModal(attempt));
        }
        
        const viewBtn = tr.querySelector('.view-btn');
        viewBtn.addEventListener('click', () => showDetailsModal(attempt));
        
        return tr;
    }

    // Format timestamp
    function formatTimestamp(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now - date;
        
        // If less than 24 hours, show relative time
        if (diff < 86400000) {
            const hours = Math.floor(diff / 3600000);
            const minutes = Math.floor((diff % 3600000) / 60000);
            
            if (hours === 0) {
                return `${minutes} min ago`;
            }
            return `${hours}h ${minutes}m ago`;
        }
        
        // Otherwise show full date
        return date.toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    // Format location
    function formatLocation(lat, lng) {
        if (!lat || !lng) return 'Unknown';
        return `${lat.toFixed(4)}, ${lng.toFixed(4)}`;
    }

    // Escape HTML to prevent XSS
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Show face modal
    function showFaceModal(attempt) {
        const modal = document.getElementById('faceModal');
        const faceImage = document.getElementById('faceImage');
        const faceEmail = document.getElementById('faceEmail');
        const faceTimestamp = document.getElementById('faceTimestamp');
        const faceIP = document.getElementById('faceIP');
        const faceLocation = document.getElementById('faceLocation');

        faceImage.src = attempt.face_image;
        faceEmail.textContent = attempt.email;
        faceTimestamp.textContent = formatTimestamp(attempt.timestamp);
        faceIP.textContent = attempt.ip_address || 'Unknown';
        faceLocation.textContent = formatLocation(attempt.latitude, attempt.longitude);

        modal.classList.add('show');
    }

    // Show details modal (reuse face modal for now)
    function showDetailsModal(attempt) {
        if (attempt.face_image) {
            showFaceModal(attempt);
        } else {
            alert(`Login Attempt Details:\n\nName: ${attempt.name}\nEmail: ${attempt.email}\nStatus: ${attempt.success ? 'Success' : 'Failed'}\nIP: ${attempt.ip_address}\nTime: ${formatTimestamp(attempt.timestamp)}`);
        }
    }

    // Close modal
    function closeModal() {
        const modal = document.getElementById('faceModal');
        modal.classList.remove('show');
    }

    // Logout function
    async function logout() {
        try {
            showLoading();
            
            const token = localStorage.getItem('auth_token');
            
            // Call logout endpoint
            await fetch(`${API_BASE_URL}/logout`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });
            
            // Clear local storage
            localStorage.removeItem('auth_token');
            localStorage.removeItem('user_email');
            localStorage.removeItem('user_name');
            
            // Clear any failed attempts counters
            Object.keys(localStorage).forEach(key => {
                if (key.startsWith('failed_attempts_')) {
                    localStorage.removeItem(key);
                }
            });
            
            hideLoading();
            redirectToLogin();
        } catch (error) {
            console.error('Logout error:', error);
            hideLoading();
            redirectToLogin();
        }
    }

    // Redirect to login
    function redirectToLogin() {
        window.location.href = '/index.html';
    }

    // Show/hide loading overlay
    function showLoading() {
        document.getElementById('loadingOverlay').classList.add('show');
    }

    function hideLoading() {
        document.getElementById('loadingOverlay').classList.remove('show');
    }

    // Event listeners
    document.getElementById('logoutBtn').addEventListener('click', logout);
    document.getElementById('refreshBtn').addEventListener('click', () => {
        showLoading();
        loadLoginAttempts().then(hideLoading);
    });
    document.getElementById('closeModal').addEventListener('click', closeModal);
    document.getElementById('modalBackdrop').addEventListener('click', closeModal);

    // Auto-refresh every 30 seconds
    setInterval(() => {
        loadLoginAttempts();
    }, 30000);
});