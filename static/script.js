// script.js - Session-based auth helper (simplified for Django sessions)

class APIClient {
    static BASE_URL = '/api/v1';

    // Fetch with CSRF token for Django
    static async fetch(endpoint, options = {}) {
        const headers = {
            'Content-Type': 'application/json',
            'X-CSRFToken': this.getCSRFToken(),
            ...options.headers
        };

        const response = await fetch(`${this.BASE_URL}${endpoint}`, {
            ...options,
            headers,
            credentials: 'include'  // Include session cookies
        });

        if (response.status === 401) {
            // Session expired
            window.location.href = '/login/';
            return null;
        }

        return response;
    }

    // Get CSRF token from cookie
    static getCSRFToken() {
        const name = 'csrftoken';
        let cookieValue = '';
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
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

// Helper to display messages
function showMessage(message, type = 'info') {
    console.log(`[${type.toUpperCase()}] ${message}`);
}