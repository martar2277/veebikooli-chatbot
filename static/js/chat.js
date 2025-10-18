// Configuration
const API_BASE_URL = '/api';

// State
let conversationId = null;
let isWaitingForResponse = false;
let awaitingConfirmation = false;
let chatStarted = false;

// DOM Elements
const chatMessages = document.getElementById('chatMessages');
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');
const progressBar = document.getElementById('progressBar');
const progressPercentage = document.getElementById('progressPercentage');
const startChatButton = document.getElementById('startChatButton');
const startChatWrapper = document.getElementById('startChatWrapper');
const statusIndicator = document.getElementById('statusIndicator');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    checkAPIHealth();
    setupEventListeners();
});

// Event Listeners
function setupEventListeners() {
    startChatButton.addEventListener('click', initializeChat);
    sendButton.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
}

// Check API health
async function checkAPIHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await response.json();
        
        if (data.status === 'healthy') {
            updateStatus('online', 'Online');
        } else {
            updateStatus('offline', 'Service Issues');
        }
    } catch (error) {
        console.error('Health check failed:', error);
        updateStatus('offline', 'Offline');
    }
}

// Update status indicator
function updateStatus(status, text) {
    const statusDot = statusIndicator.querySelector('.status-dot');
    const statusText = statusIndicator.querySelector('.status-text');
    
    statusText.textContent = text;
    
    if (status === 'online') {
        statusDot.style.background = '#48bb78';
    } else {
        statusDot.style.background = '#f56565';
    }
}

// Initialize chat
async function initializeChat() {
    try {
        startChatButton.disabled = true;
        startChatButton.textContent = 'Starting...';
        
        const response = await fetch(`${API_BASE_URL}/chat/start`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_id: null  // Anonymous user
            })
        });

        const data = await response.json();
        conversationId = data.conversation_id;
        chatStarted = true;
        
        // Remove welcome message
        chatMessages.innerHTML = '';
        
        // Display initial message
        addMessage('assistant', data.message);
        
        // Hide start button, enable input
        startChatWrapper.classList.add('hidden');
        messageInput.disabled = false;
        sendButton.disabled = false;
        messageInput.focus();
        
    } catch (error) {
        console.error('Error initializing chat:', error);
        startChatButton.disabled = false;
        startChatButton.textContent = 'Start Chat';
        alert('Failed to start chat. Please refresh and try again.');
    }
}

// Add message to chat
function addMessage(speaker, content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${speaker}`;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = speaker === 'user' ? 'Y' : 'V';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = content;
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(contentDiv);
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Show typing indicator
function showTyping() {
    const typingDiv = document.createElement('div');
    typingDiv.className = 'typing-indicator active';
    typingDiv.id = 'typingIndicator';
    typingDiv.innerHTML = '<span></span><span></span><span></span>';
    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Hide typing indicator
function hideTyping() {
    const typingIndicator = document.getElementById('typingIndicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

// Update progress bar
function updateProgress(percentage) {
    progressBar.style.width = `${percentage}%`;
    progressPercentage.textContent = `${percentage}%`;
}

// Send message
async function sendMessage() {
    const message = messageInput.value.trim();
    
    if (!message || isWaitingForResponse || !chatStarted) return;
    
    // Add user message to chat
    addMessage('user', message);
    messageInput.value = '';
    
    // Disable input
    isWaitingForResponse = true;
    sendButton.disabled = true;
    messageInput.disabled = true;
    
    // Show typing indicator
    showTyping();
    
    try {
        const response = await fetch(`${API_BASE_URL}/chat/message`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                conversation_id: conversationId,
                message: message
            })
        });

        const data = await response.json();
        
        // Hide typing indicator
        hideTyping();
        
        // Add bot response
        addMessage('assistant', data.message);
        
        // Update progress
        updateProgress(data.completion_percentage || 0);
        
        // Check if recommendation was made
        if (data.status === 'recommendation_made') {
            awaitingConfirmation = true;
            addConfirmationButtons();
        }
        
    } catch (error) {
        console.error('Error sending message:', error);
        hideTyping();
        addMessage('assistant', 'Sorry, something went wrong. Please try again.');
    } finally {
        // Re-enable input
        isWaitingForResponse = false;
        sendButton.disabled = false;
        messageInput.disabled = false;
        messageInput.focus();
    }
}

// Add confirmation buttons
function addConfirmationButtons() {
    const buttonsDiv = document.createElement('div');
    buttonsDiv.className = 'confirmation-buttons';
    buttonsDiv.id = 'confirmationButtons';
    buttonsDiv.innerHTML = `
        <button class="confirm-btn yes" onclick="confirmRecommendation(true)">
            ✓ Yes, enroll me!
        </button>
        <button class="confirm-btn no" onclick="confirmRecommendation(false)">
            ✗ Let me think about it
        </button>
    `;
    chatMessages.appendChild(buttonsDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Confirm recommendation
async function confirmRecommendation(confirmed) {
    if (!awaitingConfirmation) return;
    
    awaitingConfirmation = false;
    
    // Remove buttons
    const buttons = document.getElementById('confirmationButtons');
    if (buttons) buttons.remove();
    
    // Add user's choice as message
    addMessage('user', confirmed ? 'Yes, enroll me!' : 'Let me think about it');
    
    // Show typing
    showTyping();
    
    try {
        const response = await fetch(`${API_BASE_URL}/chat/confirm`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                conversation_id: conversationId,
                confirmed: confirmed
            })
        });

        const data = await response.json();
        
        hideTyping();
        addMessage('assistant', data.message);
        
        if (data.success) {
            updateProgress(100);
            // Disable input after successful enrollment
            setTimeout(() => {
                messageInput.disabled = true;
                sendButton.disabled = true;
                messageInput.placeholder = 'Chat completed. Refresh to start a new conversation.';
            }, 1000);
        }
        
    } catch (error) {
        console.error('Error confirming:', error);
        hideTyping();
        addMessage('assistant', 'Sorry, something went wrong. Please try again or contact support.');
    }
}

// Make confirmRecommendation available globally
window.confirmRecommendation = confirmRecommendation;