const assistant = {
    chatBox: null,
    userInput: null,
    sendBtn: null,
    isTyping: false,

    init() {
        this.chatBox = document.getElementById('chat-messages');
        this.userInput = document.getElementById('user-input');
        this.sendBtn = document.getElementById('send-btn');

        if (!this.sendBtn) return;

        this.sendBtn.addEventListener('click', () => this.sendMessage());
        this.userInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendMessage();
        });
    },

    async sendMessage() {
        const message = this.userInput.value.trim();
        if (!message || this.isTyping) return;

        this.userInput.value = '';
        this.addMessage(message, 'user');
        
        this.setTyping(true);

        try {
            const response = await fetch('/api/assistant/chat', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
                },
                body: JSON.stringify({ message })
            });

            const data = await response.json();
            this.setTyping(false);
            
            if (data.response) {
                this.addMessage(data.response, 'assistant');
            } else {
                this.addMessage("I'm sorry, I'm having trouble thinking right now. Please try again later.", 'assistant');
            }
        } catch (error) {
            console.error('Assistant Error:', error);
            this.setTyping(false);
            this.addMessage("Connection lost. Please check your internet and try again.", 'assistant');
        }
    },

    addMessage(text, sender) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${sender}`;
        
        // Simple markdown-like line break handling
        msgDiv.innerHTML = text.replace(/\n/g, '<br>');
        
        this.chatBox.appendChild(msgDiv);
        this.chatBox.scrollTop = this.chatBox.scrollHeight;
    },

    setTyping(status) {
        this.isTyping = status;
        if (status) {
            const typingDiv = document.createElement('div');
            typingDiv.className = 'message assistant typing-indicator';
            typingDiv.id = 'assistant-typing';
            typingDiv.textContent = 'Assistant is typing...';
            this.chatBox.appendChild(typingDiv);
            this.chatBox.scrollTop = this.chatBox.scrollHeight;
        } else {
            const typingDiv = document.getElementById('assistant-typing');
            if (typingDiv) typingDiv.remove();
        }
    }
};

window.assistant = assistant;
document.addEventListener('DOMContentLoaded', () => assistant.init());
