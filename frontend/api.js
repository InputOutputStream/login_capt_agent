// API Configuration and Route Management
// api.js

const API_CONFIG = {
    baseUrl: 'http://localhost:5000',
    timeout: 30000,
    headers: {
        'Content-Type': 'application/json',
    }
};

class APIClient {
    constructor(config = API_CONFIG) {
        this.baseUrl = config.baseUrl;
        this.timeout = config.timeout;
        this.headers = config.headers;
    }

    // Generic request handler
    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const config = {
            ...options,
            headers: {
                ...this.headers,
                ...options.headers,
            },
        };

        // Add timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.timeout);
        config.signal = controller.signal;

        try {
            const response = await fetch(url, config);
            clearTimeout(timeoutId);

            // Parse JSON response
            const data = await response.json();

            // Handle HTTP errors
            if (!response.ok) {
                throw new Error(data.message || data.error || `HTTP ${response.status}`);
            }

            return {
                success: true,
                data: data,
                status: response.status,
            };
        } catch (error) {
            clearTimeout(timeoutId);

            if (error.name === 'AbortError') {
                throw new Error('Request timeout');
            }

            throw new Error(error.message || 'Network error');
        }
    }

    // GET request
    async get(endpoint, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const url = queryString ? `${endpoint}?${queryString}` : endpoint;

        return this.request(url, {
            method: 'GET',
        });
    }

    // POST request
    async post(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    // PUT request
    async put(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    }

    // DELETE request
    async delete(endpoint) {
        return this.request(endpoint, {
            method: 'DELETE',
        });
    }
}

// Create API client instance
const apiClient = new APIClient();

// API Routes
const API = {
    // Authentication endpoints
    auth: {
        login: async (credentials) => {
            return apiClient.post('/login', credentials);
        },

        register: async (userData) => {
            return apiClient.post('/register', userData);
        },

        logout: async () => {
            return apiClient.post('/logout');
        },

        validateSession: async (token) => {
            return apiClient.get('/validate-session', { token });
        },
    },

    // User endpoints
    user: {
        getProfile: async (userId) => {
            return apiClient.get(`/user/${userId}`);
        },

        updateProfile: async (userId, data) => {
            return apiClient.put(`/user/${userId}`, data);
        },

        changePassword: async (userId, passwords) => {
            return apiClient.post(`/user/${userId}/change-password`, passwords);
        },

        deleteAccount: async (userId) => {
            return apiClient.delete(`/user/${userId}`);
        },
    },

    // Admin endpoints
    admin: {
        getUsers: async (page = 1, limit = 50) => {
            return apiClient.get('/admin/users', { page, limit });
        },

        getLoginAttempts: async (page = 1, limit = 100) => {
            return apiClient.get('/admin/login-attempts', { page, limit });
        },

        getAlerts: async () => {
            return apiClient.get('/admin/alerts');
        },

        resolveAlert: async (alertId) => {
            return apiClient.post(`/admin/alerts/${alertId}/resolve`);
        },
    },

    // System endpoints
    system: {
        health: async () => {
            return apiClient.get('/health');
        },

        status: async () => {
            return apiClient.get('/status');
        },

        version: async () => {
            return apiClient.get('/version');
        },
    },
};

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { API, APIClient, API_CONFIG };
}

// Export for browser
if (typeof window !== 'undefined') {
    window.API = API;
    window.APIClient = APIClient;
}