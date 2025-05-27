document.addEventListener('DOMContentLoaded', () => {
    const chatBtn = document.getElementById('chatBtn');
    const chatPopup = document.getElementById('chatPopup');
    const closeChatBtn = document.getElementById('closeChatBtn');
    const chatInput = document.getElementById('chatInput');
    const chatMessages = document.getElementById('chatMessages');
    const sendChatBtn = document.getElementById('sendChatBtn');
    const chatPanel = document.querySelector('.chat-panel');
    // Clear chat history
    const clearHistoryBtn = document.getElementById('clearHistoryBtn');
    clearHistoryBtn.addEventListener('click', () => {
        chatMessages.innerHTML = ''; // Clear all messages
    });

    // Toggle the chat popup when the "Chat" button is clicked
    chatBtn.addEventListener('click', () => {
        if (chatPopup.style.display === 'block') {
            chatPopup.style.display = 'none';
        } else {
            chatPopup.style.display = 'block';
        }
    });

    // Hide the chat popup when the close button is clicked
    closeChatBtn.addEventListener('click', () => {
        chatPopup.style.display = 'none';
    });

    // Handle sending messages
    sendChatBtn.addEventListener('click', async () => {
        const message = chatInput.value.trim();
        if (message) {
            // Display the user's message
            const userMessageElement = document.createElement('div');
            userMessageElement.innerHTML = marked.parse(`${message}`); // Render Markdown
            userMessageElement.className = 'user-message';
            chatMessages.appendChild(userMessageElement);
            chatInput.value = ''; // Clear the input field
            chatMessages.scrollTop = chatMessages.scrollHeight; // Scroll to the bottom
    
            // Send the message to the server
            try {
                const response = await fetch('/api/llama_chatbot/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCSRFToken() // Include CSRF token if needed
                    },
                    body: JSON.stringify({
                        message: message,
                        conversation_history: getConversationHistory(chatMessages)
                    })
                });
    
                if (response.ok) {
                    const data = await response.json();
                    const botMessage = data.answer || "No response from the chatbot.";
    
                    // Display the chatbot's response
                    const botMessageElement = document.createElement('div');
                    botMessageElement.innerHTML = marked.parse(`${botMessage}`); // Render Markdown
                    botMessageElement.className = 'bot-message';
                    chatMessages.appendChild(botMessageElement);
                    chatMessages.scrollTop = chatMessages.scrollHeight; // Scroll to the bottom
                } else {
                    console.error('Error:', response.statusText);
                    displayErrorMessage(chatMessages, 'Failed to get a response from the server.');
                }
            } catch (error) {
                console.error('Error:', error);
                displayErrorMessage(chatMessages, 'An error occurred while communicating with the server.');
            }
        }
    });

    // Allow pressing "Enter" to send messages
    chatInput.addEventListener('keypress', (event) => {
        if (event.key === 'Enter') {
            sendChatBtn.click();
        }
    });

    // Helper function to get CSRF token
    function getCSRFToken() {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return value;
            }
        }
        return '';
    }

    // Helper function to get conversation history
    function getConversationHistory(chatMessages) {
        const messages = [];
        chatMessages.querySelectorAll('.user-message, .bot-message').forEach((messageElement) => {
            messages.push({
                role: messageElement.className.includes('user-message') ? 'user' : 'assistant',
                content: messageElement.textContent
            });
        });
        return messages;
    }

    // Helper function to display error messages
    function displayErrorMessage(chatMessages, errorMessage) {
        const errorElement = document.createElement('div');
        errorElement.textContent = errorMessage;
        errorElement.className = 'error-message';
        chatMessages.appendChild(errorElement);
        chatMessages.scrollTop = chatMessages.scrollHeight; // Scroll to the bottom
    }
});