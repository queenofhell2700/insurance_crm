// script.js - Central authentication and API helper functions

class AuthManager {
    static TOKEN_KEY = 'authToken';

    // Save token to localStorage
    static setToken(token) {
        localStorage.setItem(this.TOKEN_KEY, token);
    }

    // Get token from localStorage
    static getToken() {
        return localStorage.getItem(this.TOKEN_KEY);
    }

    // Remove token (logout)
    static clearToken() {
        localStorage.removeItem(this.TOKEN_KEY);
    }

    // Check if user is authenticated
    static isAuthenticated() {
        return !!this.getToken();
    }

    // Decode JWT token (simple base64 decode, not cryptographically secure)
    static decodeToken() {
        const token = this.getToken();
        if (!token) return null;
        
        try {
            const payload = token.split('.')[1];
            return JSON.parse(atob(payload));
        } catch (e) {
            return null;
        }
    }

    // Get username from token
    static getUsername() {
        const decoded = this.decodeToken();
        return decoded?.username || 'User';
    }
}

class APIClient {
    static BASE_URL = '/api/v1';

    // Fetch with auth header
    static async fetch(endpoint, options = {}) {
        const token = AuthManager.getToken();
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };

        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const response = await fetch(`${this.BASE_URL}${endpoint}`, {
            ...options,
            headers
        });

        if (response.status === 401) {
            // Token expired or invalid
            AuthManager.clearToken();
            window.location.href = '/login/';
            return null;
        }

        return response;
    }

    // GET request
    static async get(endpoint) {
        const response = await this.fetch(endpoint, { method: 'GET' });
        return response?.json() || null;
    }

    // POST request
    static async post(endpoint, data) {
        const response = await this.fetch(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
        return response?.json() || null;
    }

    // PUT request
    static async put(endpoint, data) {
        const response = await this.fetch(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
        return response?.json() || null;
    }

    // DELETE request
    static async delete(endpoint) {
        const response = await this.fetch(endpoint, { method: 'DELETE' });
        return response?.json() || null;
    }
}

// Page load checks
document.addEventListener('DOMContentLoaded', function() {
    // If on dashboard, check auth
    if (window.location.pathname.includes('/dashboard/')) {
        if (!AuthManager.isAuthenticated()) {
            window.location.href = '/login/';
        }
    }

    // If on login/signup but already authenticated, redirect to dashboard
    if ((window.location.pathname.includes('/login/') || window.location.pathname.includes('/signup/')) && AuthManager.isAuthenticated()) {
        window.location.href = '/dashboard/';
    }
});