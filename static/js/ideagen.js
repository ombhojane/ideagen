    const ideasContainer = document.getElementById('ideas-container');

    let currentIdeaIndex = -1;

    function openChatModal(event) {
        currentIdeaIndex = event.target.getAttribute('data-id');
        document.getElementById('chatModal').style.display = 'block';
        document.getElementById('chatHistory').innerHTML = '';
        document.getElementById('chatInput').value = '';
    }

    function closeChatModal() {
        document.getElementById('chatModal').style.display = 'none';
    }

    // At the top of your JavaScript file, add this line:

    // Update the sendChatMessage function:
    async function sendChatMessage() {
        const chatInput = document.getElementById('chatInput');
        const chatHistory = document.getElementById('chatHistory');
        const query = chatInput.value.trim();
        if (!query) return;

        // Display user message
        displayChatMessage(query, null);

        // Show loading indicator
        const loadingMessage = document.createElement('div');
        loadingMessage.className = 'chat-message ai-message loading';
        loadingMessage.textContent = 'Thinking...';
        chatHistory.appendChild(loadingMessage);
        chatHistory.scrollTop = chatHistory.scrollHeight;

        try {
            const idea = ideasContainer.querySelectorAll('.idea')[currentIdeaIndex];
            const ideaText = idea.innerText;

            const response = await fetch('/chat_with_idea', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: query,
                    idea: ideaText,
                    category: document.getElementById('category').value,
                    proficiency: document.getElementById('proficiency').value,
                    time_frame: document.getElementById('time-frame').value,
                    team_size: parseInt(document.getElementById('team-size').value),
                    technical_skills: Array.from(document.querySelectorAll('input[name="technical-skills"]:checked')).map(checkbox => checkbox.value),
                    project_goals: [document.querySelector('input[name="project-goals"]:checked').value],
                    theme: document.getElementById('theme').value
                }),
            });

            if (!response.ok) {
                throw new Error('Network response was not ok');
            }

            const data = await response.json();
            
            // Remove loading indicator
            loadingMessage.remove();
            
            // Display AI response
            displayChatMessage(null, data.response);
            chatInput.value = '';
        } catch (error) {
            console.error('Error:', error);
            // Remove loading indicator
            loadingMessage.remove();
            // Display error message
            displayChatMessage(null, 'Failed to send message. Please try again.');
        }
    }

    function displayChatMessage(query, response) {
        const chatHistory = document.getElementById('chatHistory');
        if (query) {
            const userMessageDiv = document.createElement('div');
            userMessageDiv.className = 'chat-message user-message';
            userMessageDiv.textContent = query;
            chatHistory.appendChild(userMessageDiv);
        }
        if (response) {
            const aiMessageDiv = document.createElement('div');
            aiMessageDiv.className = 'chat-message ai-message';
            aiMessageDiv.textContent = response;
            chatHistory.appendChild(aiMessageDiv);
        }
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    // Add event listeners for chat modal
    document.querySelector('.close').addEventListener('click', closeChatModal);
    document.getElementById('sendChatButton').addEventListener('click', sendChatMessage);
    document.getElementById('chatInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendChatMessage();
        }
    });