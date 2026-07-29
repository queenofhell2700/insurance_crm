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


// Chat functionality
function sendChatMessage() {
    const input = document.getElementById('chatInput');
    const messagesContainer = document.getElementById('chatMessages');
    const question = input.value.trim();
    const customerId = input.dataset.customerId;
    if (!question || !customerId) return;

    // Show user message
    appendMessage('user', question);
    input.value = '';

    // Show loading
    appendMessage('assistant', '? Thinking...');

    // Call API
    fetch('/api/v1/ai/chat/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': APIClient.getCSRFToken()
        },
        body: JSON.stringify({ customer_id: customerId, question: question })
    })
    .then(response => response.json())
    .then(data => {
        // Remove loading message (last child)
        const messages = messagesContainer.querySelectorAll('.message-bubble');
        if (messages.length > 0 &&
            messages[messages.length-1].textContent.includes('?')) {
            messages[messages.length-1].remove();
        }
        if (data.status === 'success') {
            appendMessage('assistant', data.data.answer);
        } else {
            appendMessage('assistant', '? Error: ' + (data.message || 'Unknown error'));
        }
    })
    .catch(error => {
        appendMessage('assistant', '? Failed to reach server.');
    });
}

function appendMessage(role, text) {
    const container = document.getElementById('chatMessages');
    const div = document.createElement('div');
    div.className = 'chat-message';
    div.innerHTML = `<div class="message-bubble ${role}">${text}</div>`;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

// Allow pressing Enter to send
document.addEventListener('DOMContentLoaded', function() {
    const input = document.getElementById('chatInput');
    if (input) {
        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') sendChatMessage();
        });
    }
});