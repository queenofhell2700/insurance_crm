// Dashboard JavaScript - Wires up chat, insights, and customer interactions

document.addEventListener('DOMContentLoaded', function() {
    // Initialize chat functionality
    initializeChatHandler();
    
    // Load customer list if sidebar exists
    loadCustomerList();
    
    // Auto-focus chat input
    const chatInput = document.getElementById('chatInput');
    if (chatInput) {
        chatInput.focus();
    }
});

// ============ CHAT FUNCTIONALITY ============

function initializeChatHandler() {
    const chatInput = document.getElementById('chatInput');
    if (!chatInput) return;
    
    // Send message on Enter key
    chatInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendChatMessage();
        }
    });
}

function sendChatMessage() {
    const chatInput = document.getElementById('chatInput');
    const chatMessages = document.getElementById('chatMessages');
    
    if (!chatInput || !chatMessages) return;
    
    const message = chatInput.value.trim();
    if (!message) return;
    
    const customerId = chatInput.getAttribute('data-customer-id');
    if (!customerId) {
        alert('Please select a customer first');
        return;
    }
    
    // Add user message to chat
    addChatMessage(message, 'user');
    chatInput.value = '';
    
    // Send to backend
    fetch('/api/ai/chat/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify({
            customer_id: customerId,
            message: message
        })
    })
    .then(response => {
        if (!response.ok) throw new Error('Chat request failed');
        return response.json();
    })
    .then(data => {
        // Add AI response to chat
        addChatMessage(data.response || data.message || 'No response', 'assistant');
    })
    .catch(error => {
        console.error('Chat error:', error);
        addChatMessage('Sorry, I encountered an error. Please try again.', 'assistant');
    });
}

function addChatMessage(text, sender) {
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = 'chat-message';
    
    const bubble = document.createElement('div');
    bubble.className = `message-bubble ${sender}`;
    bubble.textContent = text;
    
    messageDiv.appendChild(bubble);
    chatMessages.appendChild(messageDiv);
    
    // Auto-scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// ============ CUSTOMER LIST FUNCTIONALITY ============

function loadCustomerList() {
    // Fetch customers and populate sidebar if it exists
    const customerList = document.getElementById('customerList');
    if (!customerList) return;
    
    fetch('/api/v1/customers/', {
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
        }
    })
    .then(response => {
        if (!response.ok) throw new Error('Failed to load customers');
        return response.json();
    })
    .then(data => {
        const customers = data.results || data;
        customerList.innerHTML = '';
        
        customers.forEach(customer => {
            const customerItem = document.createElement('div');
            customerItem.className = 'customer-list-item';
            customerItem.innerHTML = `
                <div class="customer-name">${customer.full_name}</div>
                <div class="customer-meta">${customer.city || 'N/A'}</div>
            `;
            customerItem.addEventListener('click', function() {
                selectCustomer(customer.id);
            });
            customerList.appendChild(customerItem);
        });
    })
    .catch(error => {
        console.error('Error loading customers:', error);
        if (customerList) {
            customerList.innerHTML = '<div class="error-message">Failed to load customers</div>';
        }
    });
}

function selectCustomer(customerId) {
    // Navigate to dashboard with selected customer
    window.location.href = `/dashboard/?customer_id=${customerId}`;
}

// ============ INSIGHTS FUNCTIONALITY ============

function generateInsights(customerId) {
    if (!customerId) {
        alert('Please select a customer first');
        return;
    }
    
    const btn = event.target;
    btn.disabled = true;
    btn.textContent = 'Generating...';
    
    fetch(`/api/v1/customers/qualification-insights/generate/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify({
            customer_id: customerId
        })
    })
    .then(response => {
        if (!response.ok) throw new Error('Failed to generate insights');
        return response.json();
    })
    .then(data => {
        // Reload page to show new insights
        setTimeout(() => {
            window.location.reload();
        }, 1000);
    })
    .catch(error => {
        console.error('Error generating insights:', error);
        btn.disabled = false;
        btn.textContent = 'Generate Insights';
        alert('Failed to generate insights. Please try again.');
    });
}

function generateQuestions(customerId) {
    if (!customerId) {
        alert('Please select a customer first');
        return;
    }
    
    const btn = event.target;
    btn.disabled = true;
    btn.textContent = 'Generating...';
    
    fetch(`/api/v1/customers/question-suggestions/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify({
            customer_id: customerId
        })
    })
    .then(response => {
        if (!response.ok) throw new Error('Failed to generate questions');
        return response.json();
    })
    .then(data => {
        // Reload page to show new questions
        setTimeout(() => {
            window.location.reload();
        }, 1000);
    })
    .catch(error => {
        console.error('Error generating questions:', error);
        btn.disabled = false;
        btn.textContent = 'Generate Questions';
        alert('Failed to generate questions. Please try again.');
    });
}

// ============ UTILITY FUNCTIONS ============

function getCookie(name) {
    let cookieValue = null;
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

// Export functions for inline onclick handlers
window.sendChatMessage = sendChatMessage;
window.selectCustomer = selectCustomer;
window.generateInsights = generateInsights;
window.generateQuestions = generateQuestions;