document.addEventListener('DOMContentLoaded', () => {
    const chatbox = document.getElementById('chatbox');
    const messageForm = document.getElementById('messageForm');
    const userInput = document.getElementById('userInput');
    const errorMessage = document.getElementById('errorMessage');
    const langSwitchBtn = document.getElementById('langSwitchBtn');

    /**
     * Adds a message to the chatbox.
     * @param {string} sender - 'user' or 'bot'
     * @param {string} text - The message text
     * @param {string} [userMessage] - The original user message (only for bot replies)
     */
    function addMessage(sender, text, userMessage = null) {
        const messageWrapper = document.createElement('div');
        messageWrapper.classList.add('message', sender);
        
        // Add text content
        const messageText = document.createElement('span');
        messageText.textContent = text;
        messageWrapper.appendChild(messageText);

        // If it's a bot message (and not the initial welcome), add feedback UI
        if (sender === 'bot' && userMessage) {
            const feedbackContainer = document.createElement('div');
            feedbackContainer.classList.add('feedback-container');

            // 1. The Buttons Container
            const buttonsDiv = document.createElement('div');
            buttonsDiv.classList.add('feedback-buttons');
            
            // Helper to create buttons
            const createFeedbackBtn = (ratingType) => {
                const btn = document.createElement('button');
                btn.classList.add('feedback-btn', ratingType === 'good' ? 'thumb-up' : 'thumb-down');
                btn.dataset.rating = ratingType;
                // SVG Icons
                btn.innerHTML = ratingType === 'good' 
                    ? '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"></path></svg>'
                    : '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 15v7a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zM17 2h3a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2h-3"></path></svg>';
                
                btn.addEventListener('click', () => {
                    // Hide buttons, show comment box
                    buttonsDiv.style.display = 'none';
                    commentDiv.style.display = 'flex';
                    // Store rating on the comment div for later retrieval
                    commentDiv.dataset.rating = ratingType;
                    // Small delay to ensure element is visible before focusing
                    setTimeout(() => commentInput.focus(), 50); 
                });
                return btn;
            };

            const thumbUpBtn = createFeedbackBtn('good');
            const thumbDownBtn = createFeedbackBtn('bad');
            
            buttonsDiv.appendChild(thumbUpBtn);
            buttonsDiv.appendChild(thumbDownBtn);
            feedbackContainer.appendChild(buttonsDiv);

            // 2. The Comment Box (Hidden initially)
            const commentDiv = document.createElement('div');
            commentDiv.classList.add('feedback-comment-box');
            // Style handles display:none via CSS class usually, but ensure it here
            commentDiv.style.display = 'none'; 

            const commentInput = document.createElement('input');
            commentInput.type = 'text';
            commentInput.placeholder = 'Why did you rate this? (Optional)';
            
            const submitBtn = document.createElement('button');
            submitBtn.textContent = 'Submit';

            commentDiv.appendChild(commentInput);
            commentDiv.appendChild(submitBtn);
            feedbackContainer.appendChild(commentDiv);

            messageWrapper.appendChild(feedbackContainer);

            // 3. Submit Feedback Logic
            const sendFeedback = async () => {
                const rating = commentDiv.dataset.rating;
                const comment = commentInput.value.trim();
                
                // Show visual feedback immediately
                feedbackContainer.innerHTML = '<span class="feedback-thanks">Thanks for your feedback!</span>';

                try {
                    await fetch('/feedback', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            user_message: userMessage,
                            bot_response: text,
                            rating: rating,
                            comment: comment
                        }),
                    });
                } catch (error) {
                    console.error('Feedback error:', error);
                }
            };

            submitBtn.addEventListener('click', sendFeedback);
            commentInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault(); // Prevent chat form submit
                    sendFeedback();
                }
            });
        }

        chatbox.appendChild(messageWrapper);
        chatbox.scrollTop = chatbox.scrollHeight;
    }

    // Handle sending messages
    if (messageForm) {
        messageForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            const messageText = userInput.value.trim();
            errorMessage.textContent = ''; // Clear errors

            if (!messageText) return;

            addMessage('user', messageText); // Display user's message
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
                    // Pass both bot reply AND original user message so feedback works
                    addMessage('bot', data.reply, messageText); 
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
    }

    // --- Language Switcher Logic ---
    if (langSwitchBtn) {
        langSwitchBtn.addEventListener('click', async () => {
            const currentLang = langSwitchBtn.dataset.current;
            const newLang = currentLang === 'en' ? 'hi' : 'en'; // Toggle
            
            langSwitchBtn.disabled = true;
            langSwitchBtn.textContent = "Switching...";

            try {
                // Use PUT /profile to update the language
                const response = await fetch('/profile', {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ preferred_language: newLang })
                });

                if (response.ok) {
                    window.location.reload(); // Reload page to update UI language
                } else {
                    alert("Failed to switch language.");
                    // Revert button state on failure
                    langSwitchBtn.disabled = false;
                    langSwitchBtn.textContent = currentLang === 'en' ? 'Switch to Hindi (हिन्दी)' : 'Switch to English';
                }
            } catch (error) {
                console.error("Language switch error:", error);
                alert("Error connecting to server.");
                langSwitchBtn.disabled = false;
                langSwitchBtn.textContent = currentLang === 'en' ? 'Switch to Hindi (हिन्दी)' : 'Switch to English';
            }
        });
    }
});