// API Configuration
const API_URL = 'http://localhost:5000';

// Utility Functions
function showLoading(elementId, message = 'Loading...') {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `
            <div class="loading-spinner">
                <span class="spinner"></span>
                <span>${message}</span>
            </div>
        `;
    }
}

function showError(elementId, message) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `
            <div class="error-message">
                ❌ ${message}
            </div>
        `;
    }
}

function showSuccess(elementId, message) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `
            <div class="success-message">
                ✅ ${message}
            </div>
        `;
    }
}

// Date/Time Formatting
function formatDateTime(isoString) {
    const date = new Date(isoString);
    return date.toLocaleString();
}

function formatDate(isoString) {
    const date = new Date(isoString);
    return date.toLocaleDateString();
}

// API Helper Functions
async function apiCall(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_URL}${endpoint}`, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('API call failed:', error);
        throw error;
    }
}

// Check API status
async function checkAPIStatus() {
    try {
        const response = await fetch(`${API_URL}/api/health`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        
        if (data.success && data.status === 'online') {
            console.log('✅ API is online');
            showAPIStatus(true);
            return true;
        } else {
            throw new Error('API returned invalid status');
        }
    } catch (error) {
        console.error('❌ API is offline:', error.message);
        showAPIStatus(false);
        return false;
    }
}

function showAPIStatus(isOnline) {
    // Remove any existing status indicator
    const existingIndicator = document.getElementById('api-status-indicator');
    if (existingIndicator) {
        existingIndicator.remove();
    }

    // Create new status indicator
    const indicator = document.createElement('div');
    indicator.id = 'api-status-indicator';
    indicator.style.cssText = `
        position: fixed;
        top: 10px;
        right: 10px;
        padding: 10px 20px;
        border-radius: 25px;
        font-weight: bold;
        z-index: 9999;
        display: flex;
        align-items: center;
        gap: 8px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
    `;

    if (isOnline) {
        indicator.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
        indicator.style.color = 'white';
        indicator.innerHTML = '<span style="font-size: 12px;">🟢</span> API Online';
    } else {
        indicator.style.background = 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)';
        indicator.style.color = 'white';
        indicator.innerHTML = '<span style="font-size: 12px;">🔴</span> API Offline';
    }

    document.body.appendChild(indicator);
}

// Safe fetch wrapper
async function safeFetch(url, options = {}) {
    try {
        const response = await fetch(url, {
            ...options,
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                ...options.headers
            }
        });

        // Check if response is JSON
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            throw new Error('Server returned non-JSON response. API might be offline.');
        }

        const data = await response.json();
        return data;

    } catch (error) {
        console.error('Fetch error:', error);
        
        // Show user-friendly error
        if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
            showNotification('❌ Cannot connect to API. Is the server running?', 'error');
        } else {
            showNotification(`❌ Error: ${error.message}`, 'error');
        }
        
        return { success: false, error: error.message };
    }
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 80px;
        right: 20px;
        padding: 15px 25px;
        border-radius: 10px;
        z-index: 10000;
        max-width: 400px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        animation: slideIn 0.3s ease;
    `;

    if (type === 'error') {
        notification.style.background = '#f8d7da';
        notification.style.color = '#721c24';
        notification.style.border = '2px solid #f5c6cb';
    } else if (type === 'success') {
        notification.style.background = '#d4edda';
        notification.style.color = '#155724';
        notification.style.border = '2px solid #c3e6cb';
    } else {
        notification.style.background = '#d1ecf1';
        notification.style.color = '#0c5460';
        notification.style.border = '2px solid #bee5eb';
    }

    notification.textContent = message;
    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}

// Add CSS animation
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    checkAPIStatus();
    
    // Recheck every 30 seconds
    setInterval(checkAPIStatus, 30000);
});

// Export for use in other files
window.API_URL = API_URL;
window.safeFetch = safeFetch;
window.checkAPIStatus = checkAPIStatus;
window.showNotification = showNotification;