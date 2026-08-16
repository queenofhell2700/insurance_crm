// Dashboard JavaScript - Wires up chat, insights, and customer interactions

// ============================================
// ADDED: Dashboard Stats - Dynamic Data Loading
// ============================================

/**
 * WHY: These functions fetch REAL data from your database
 * and update the dashboard overview numbers dynamically
 */

// Function to load dashboard stats from API
async function loadDashboardStats() {
    try {
        const response = await fetch('/api/dashboard/stats/');
        const result = await response.json();
        
        if (result.status === 'success') {
            const data = result.data;
            
            // Update the 4 main metric cards
            const totalCustomersEl = document.querySelector('.metric-card:nth-child(1) .metric-value');
            const activePoliciesEl = document.querySelector('.metric-card:nth-child(2) .metric-value');
            const qualifiedLeadsEl = document.querySelector('.metric-card:nth-child(3) .metric-value');
            const conversionRateEl = document.querySelector('.metric-card:nth-child(4) .metric-value');
            
            // Update values
            if (totalCustomersEl) totalCustomersEl.textContent = data.total_customers;
            if (activePoliciesEl) activePoliciesEl.textContent = data.active_policies;
            
            // Update growth percentages
            const growthSpans = document.querySelectorAll('.metric-change');
            if (growthSpans.length >= 4) {
                // Customer growth
                growthSpans[0].textContent = data.customer_growth >= 0 ? 
                    `▲ ${data.customer_growth}% vs last month` : 
                    `▼ ${Math.abs(data.customer_growth)}% vs last month`;
                growthSpans[0].className = `metric-change ${data.customer_growth >= 0 ? 'up' : 'down'}`;
                
                // Policy growth
                growthSpans[1].textContent = data.policy_growth >= 0 ? 
                    `▲ ${data.policy_growth}% vs last month` : 
                    `▼ ${Math.abs(data.policy_growth)}% vs last month`;
                growthSpans[1].className = `metric-change ${data.policy_growth >= 0 ? 'up' : 'down'}`;
            }
        }
    } catch (error) {
        console.error('Error loading dashboard stats:', error);
    }
}

// Function to load monthly customer data for the bar chart
async function loadMonthlyChartData() {
    try {
        const response = await fetch('/api/dashboard/monthly-customers/');
        const result = await response.json();
        
        if (result.status === 'success') {
            const data = result.data;
            
            // Update the bar chart
            const chartCanvas = document.getElementById('overviewBarChart');
            if (chartCanvas && window.barChart) {
                window.barChart.data.labels = data.labels;
                window.barChart.data.datasets[0].data = data.values;
                window.barChart.update();
            }
        }
    } catch (error) {
        console.error('Error loading monthly chart data:', error);
    }
}

// Function to load policy mix data for the donut chart
async function loadPolicyMixChartData() {
    try {
        const response = await fetch('/api/dashboard/policy-mix/');
        const result = await response.json();
        
        if (result.status === 'success') {
            const data = result.data;
            
            // Update the donut chart
            const chartCanvas = document.getElementById('overviewDonutChart');
            if (chartCanvas && window.donutChart) {
                window.donutChart.data.labels = data.labels;
                window.donutChart.data.datasets[0].data = data.values;
                window.donutChart.update();
            }
        }
    } catch (error) {
        console.error('Error loading policy mix chart data:', error);
    }
}
//end of added chunk

// document.addEventListener('DOMContentLoaded', function() {
//     // Initialize chat functionality
//     initializeChatHandler();
//     
//     // Load customer list if sidebar exists
//     loadCustomerList();
//     
//     // Auto-focus chat input
//     const chatInput = document.getElementById('chatInput');
//     if (chatInput) {
//         chatInput.focus();
//     }
// });


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
    
    // ===== ADDED: Load dashboard stats dynamically =====
    loadDashboardStats();
    loadMonthlyChartData();
    loadPolicyMixChartData();
    
    // Auto-refresh stats every 60 seconds (optional)
    setInterval(loadDashboardStats, 60000);
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
    //fetch('/api/ai/chat/', {
    fetch('/api/v1/ai/chat/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify({
            customer_id: customerId,
            question: message
        })
    })
    .then(response => {
        if (!response.ok) throw new Error('Chat request failed');
        return response.json();
    })
    .then(data => {
        // Add AI response to chat
        addChatMessage(data.data.answer || 'No response', 'assistant');
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