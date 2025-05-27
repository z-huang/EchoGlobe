$(function () {
    const $chatBtn = $('#chatBtn');
    const $chatPopup = $('#chatPopup');
    const $closeChatBtn = $('#closeChatBtn');
    const $chatInput = $('#chatInput');
    const $chatMessages = $('#chatMessages');
    const $sendChatBtn = $('#sendChatBtn');
    const $clearHistoryBtn = $('#clearHistoryBtn');

    // Clear chat history
    $clearHistoryBtn.on('click', function () {
        $chatMessages.empty();
    });

    // Toggle the chat popup when the "Chat" button is clicked
    $chatBtn.on('click', function () {
        $chatPopup.toggle();
    });

    // Hide the chat popup when the close button is clicked
    $closeChatBtn.on('click', function () {
        $chatPopup.hide();
    });

    // Handle sending messages
    $sendChatBtn.on('click', async function () {
        const message = $chatInput.val().trim();
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
                        'X-CSRFToken': getCSRFToken()
                    },
                    body: JSON.stringify({
                        message: message,
                        conversation_history: getConversationHistory($chatMessages)
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
                    displayErrorMessage($chatMessages, 'Failed to get a response from the server.');
                }
            } catch (error) {
                console.error('Error:', error);
                displayErrorMessage($chatMessages, 'An error occurred while communicating with the server.');
            }
        }
    });

    // Allow pressing "Enter" to send messages
    $chatInput.on('keypress', function (event) {
        if (event.key === 'Enter') {
            $sendChatBtn.click();
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
    function getConversationHistory($chatMessages) {
        const messages = [];
        $chatMessages.find('.user-message, .bot-message').each(function () {
            messages.push({
                role: $(this).hasClass('user-message') ? 'user' : 'assistant',
                content: $(this).text()
            });
        });
        return messages;
    }

    // Helper function to display error messages
    function displayErrorMessage($chatMessages, errorMessage) {
        const $errorElement = $('<div>')
            .text(errorMessage)
            .addClass('error-message');
        $chatMessages.append($errorElement);
        $chatMessages.scrollTop($chatMessages[0].scrollHeight);
    }
});
