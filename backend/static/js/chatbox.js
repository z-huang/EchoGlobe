document.addEventListener('DOMContentLoaded', () => {
    const chatBtn = document.getElementById('chatBtn');
    const chatPopup = document.getElementById('chatPopup');
    const closeChatBtn = document.getElementById('closeChatBtn');
    const chatInput = document.getElementById('chatInput');
    const chatMessages = document.getElementById('chatMessages');
    const sendChatBtn = document.getElementById('sendChatBtn');
    const chatPanel = document.querySelector('.chat-panel');

    // Toggle the chat popup when the "Chat" button is clicked
    chatBtn.addEventListener('click', () => {
        if (chatPopup.style.display === 'block') {
            // Hide the chat popup if it is already visible
            chatPopup.style.display = 'none';
        } else {
            // Calculate the position relative to the chat panel and show the chat popup
            chatPopup.style.display = 'block';
        }
    });

    // Hide the chat popup when the close button is clicked
    closeChatBtn.addEventListener('click', () => {
        chatPopup.style.display = 'none';
    });

    // Handle sending messages
    sendChatBtn.addEventListener('click', () => {
        const message = chatInput.value.trim();
        if (message) {
            const messageElement = document.createElement('div');
            messageElement.textContent = message;
            messageElement.className = 'user-message';
            chatMessages.appendChild(messageElement);
            chatInput.value = ''; // Clear the input field
            chatMessages.scrollTop = chatMessages.scrollHeight; // Scroll to the bottom
        }
    });

    // Allow pressing "Enter" to send messages
    chatInput.addEventListener('keypress', (event) => {
        if (event.key === 'Enter') {
            sendChatBtn.click();
        }
    });
});