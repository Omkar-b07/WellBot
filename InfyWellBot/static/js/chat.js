document.addEventListener('DOMContentLoaded', () => {
    const chatbox = document.getElementById('chatbox');
    const messageForm = document.getElementById('messageForm');
    const userInput = document.getElementById('userInput');
    const errorMessage = document.getElementById('errorMessage');

    // Function to add a message to the chatbox
    function addMessage(sender, text) {
        const messageDiv = document.createElement('div');
        // Add classes for styling (e.g., 'message bot' or 'message user')
        messageDiv.classList.add('message', sender);
        // *** ADD THIS LINE ***
        messageDiv.textContent = text; // Set the actual text content
        // *** END FIX ***
        chatbox.appendChild(messageDiv);
        // Scroll to the bottom
        chatbox.scrollTop = chatbox.scrollHeight;
    }

    // Handle sending messages
    messageForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const messageText = userInput.value.trim();
        errorMessage.textContent = ''; // Clear errors

        if (!messageText) return;

        addMessage('user', messageText); // Display user message
        userInput.value = ''; // Clear input

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: messageText }),
            });

            const data = await response.json();

            if (response.ok) {
                // Make sure data.reply exists and is passed correctly
                addMessage('bot', data.reply);
            } else {
                errorMessage.textContent = data.error || data.msg || 'Error sending message.';
                if (response.status === 401 || response.status === 422 ) {
                     window.location.href = '/login_page';
                }
            }
        } catch (error) {
            console.error('Chat error:', error);
            errorMessage.textContent = 'Could not connect to the server.';
        }
    });


    addMessage('bot', "Hello! I'm your wellness assistant. You can ask me about symptoms, first-aid, or general wellness tips.");

});

