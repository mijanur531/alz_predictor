/**
 * Clinical AI Chatbot Client (RAG + NLP + LLM)
 * Handles conversational queries, DOM event bindings, source citations, and action links.
 */

document.addEventListener('DOMContentLoaded', function() {
    const fabBtn = document.getElementById('chatbot-fab-btn');
    const windowEl = document.getElementById('chatbot-window');
    const closeBtn = document.getElementById('chatbot-close-btn');
    const form = document.getElementById('chatbot-form');
    const input = document.getElementById('chatbot-input');
    const messagesContainer = document.getElementById('chatbot-messages');
    const typingIndicator = document.getElementById('chatbot-typing-indicator');

    if (!fabBtn || !windowEl || !form) return;

    // Toggle Chatbot Window
    fabBtn.addEventListener('click', () => {
        const isHidden = windowEl.classList.contains('d-none');
        if (isHidden) {
            windowEl.classList.remove('d-none');
            windowEl.classList.add('d-flex');
            input.focus();
        } else {
            windowEl.classList.add('d-none');
            windowEl.classList.remove('d-flex');
        }
    });

    closeBtn.addEventListener('click', () => {
        windowEl.classList.add('d-none');
        windowEl.classList.remove('d-flex');
    });

    // Quick starter prompt pills
    document.querySelectorAll('.quick-prompt-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const query = this.getAttribute('data-query');
            if (query) {
                sendMessage(query);
            }
        });
    });

    // Form submission
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        const text = input.value.trim();
        if (!text) return;
        input.value = '';
        sendMessage(text);
    });

    async function sendMessage(text) {
        // 1. Append User Message
        appendUserMessage(text);
        
        // 2. Show Typing Indicator
        typingIndicator.classList.remove('d-none');
        typingIndicator.classList.add('d-flex');
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        try {
            const csrfToken = getCookie('csrftoken') || '';
            const response = await fetch('/api/v1/chatbot/query/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({ message: text })
            });

            const data = await response.json();
            
            // 3. Hide Typing Indicator
            typingIndicator.classList.add('d-none');
            typingIndicator.classList.remove('d-flex');

            if (response.ok) {
                appendAssistantMessage(data);
            } else {
                appendErrorMessage(data.detail || 'Unable to process query. Please try again.');
            }
        } catch (err) {
            typingIndicator.classList.add('d-none');
            typingIndicator.classList.remove('d-flex');
            appendErrorMessage('Network connection error. Please verify your connection.');
        }

        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    function appendUserMessage(text) {
        const msgDiv = document.createElement('div');
        msgDiv.className = 'd-flex gap-2 justify-content-end align-items-start';
        msgDiv.innerHTML = `
            <div class="p-3 rounded-4 bg-primary text-white shadow-sm" style="max-width: 82%;">
                <p class="mb-0">${escapeHtml(text)}</p>
            </div>
            <div class="rounded-circle bg-primary bg-opacity-50 p-1 flex-shrink-0 text-white" style="width: 28px; height: 28px; text-align: center; font-size: 0.8rem;">👤</div>
        `;
        messagesContainer.appendChild(msgDiv);
    }

    function appendAssistantMessage(data) {
        const msgDiv = document.createElement('div');
        msgDiv.className = 'd-flex gap-2 align-items-start';

        // Format RAG sources citation badges
        let sourcesHtml = '';
        if (data.retrieved_sources && data.retrieved_sources.length > 0) {
            sourcesHtml = '<div class="mt-2 pt-2 border-top border-secondary small text-muted"><strong>📚 Sources:</strong> ' +
                data.retrieved_sources.map(s => `<span class="badge bg-secondary bg-opacity-50 text-info me-1">${s}</span>`).join('') +
                '</div>';
        }

        // Format Action Buttons
        let actionsHtml = '';
        if (data.actions && data.actions.length > 0) {
            actionsHtml = '<div class="d-flex flex-wrap gap-1 mt-2 pt-2 border-top border-secondary">' +
                data.actions.map(a => `<a href="${a.url}" class="btn btn-xs btn-outline-info rounded-pill text-decoration-none">${a.label}</a>`).join('') +
                '</div>';
        }

        // Convert simple markdown line breaks to HTML
        let formattedText = escapeHtml(data.response)
            .replace(/\n\n/g, '<br><br>')
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

        msgDiv.innerHTML = `
            <div class="rounded-circle bg-info bg-opacity-25 p-1 flex-shrink-0" style="width: 28px; height: 28px; text-align: center; font-size: 0.8rem;">🤖</div>
            <div class="p-3 rounded-4 bg-secondary bg-opacity-25 border border-secondary text-light" style="max-width: 85%;">
                <p class="mb-0">${formattedText}</p>
                ${sourcesHtml}
                ${actionsHtml}
            </div>
        `;
        messagesContainer.appendChild(msgDiv);
    }

    function appendErrorMessage(errorText) {
        const msgDiv = document.createElement('div');
        msgDiv.className = 'd-flex gap-2 align-items-start';
        msgDiv.innerHTML = `
            <div class="rounded-circle bg-danger bg-opacity-25 p-1 flex-shrink-0" style="width: 28px; height: 28px; text-align: center; font-size: 0.8rem;">⚠️</div>
            <div class="p-3 rounded-4 bg-danger bg-opacity-10 border border-danger text-danger small">
                ${escapeHtml(errorText)}
            </div>
        `;
        messagesContainer.appendChild(msgDiv);
    }

    function escapeHtml(str) {
        if (!str) return '';
        return str.replace(/[&<>'"]/g, 
            tag => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[tag] || tag)
        );
    }

    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return '';
    }
});
