const chatMessages = document.getElementById('chat-messages');
const form = document.getElementById('question-form');
const questionInput = document.getElementById('question');

document.addEventListener('DOMContentLoaded', function() {
    form.addEventListener('submit', async function(event) {
        event.preventDefault();

        const question = questionInput.value.trim();
        if (!question) {
            return;
        }

        addMessage('user', question);
        questionInput.value = '';
        questionInput.focus();

        const assistantBubble = addMessage('assistant', '');
        setFormEnabled(false);

        try {
            const formData = new FormData();
            formData.append('question', question);

            const response = await fetch('/generate', {
                method: 'POST',
                body: formData
            });

            if (!response.ok || !response.body) {
                const errorText = await response.text();
                throw new Error(errorText || 'Unable to generate a response.');
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let assistantText = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) {
                    break;
                }

                assistantText += decoder.decode(value, { stream: true });
                assistantBubble.innerHTML = assistantText;
                scrollToBottom();
            }

            if (assistantText.trim()) {
                await saveAssistantResponse(assistantText);
            }
        } catch (error) {
            assistantBubble.textContent = 'Sorry, I could not generate a response. Please try again.';
            console.error('Assistant error:', error);
        } finally {
            setFormEnabled(true);
            questionInput.focus();
        }
    });
});

window.onload = () => {
    fetch('/assistantAPI/get_session', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        },
        credentials: 'include'
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            showOutput('Welcome Guest');
            closePopup();
        } else {
            showPopup();
        }
    })
    .catch(error => {
        console.error('Session check failed:', error);
        showPopup();
    });
};

function addMessage(role, text) {
    const message = document.createElement('div');
    message.className = `chat-message ${role}-message`;

    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';

    if (role === 'user') {
        bubble.textContent = text;
    } else {
        bubble.innerHTML = text;
    }

    message.appendChild(bubble);
    chatMessages.appendChild(message);
    scrollToBottom();

    return bubble;
}

function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

async function saveAssistantResponse(assistantText) {
    const response = await fetch('/assistantAPI/response', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify({ message: assistantText })
    });

    if (!response.ok) {
        throw new Error('Unable to save assistant response.');
    }
}

function setFormEnabled(enabled) {
    questionInput.disabled = !enabled;
    form.querySelector('button[type="submit"]').disabled = !enabled;
}

function showPopup() {
    document.getElementById('popup').style.display = 'flex';
    document.body.classList.add('modal-open');
    document.getElementById('main-content').classList.remove('active');
}

function closePopup() {
    document.getElementById('popup').style.display = 'none';
    document.body.classList.remove('modal-open');
    document.getElementById('main-content').classList.add('active');
}

function showOutput(data) {
    document.getElementById('output').textContent =
        typeof data === 'string' ? data : JSON.stringify(data, null, 2);
}

function setGuestToken() {
    fetch('/assistantAPI/set_session', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        },
        credentials: 'include'
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            showOutput('Welcome Guest');
            closePopup();
            questionInput.focus();
        } else {
            showPopup();
        }
    })
    .catch(error => {
        console.error('Session setup failed:', error);
        showPopup();
    });
}
