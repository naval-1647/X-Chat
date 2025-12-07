// ChatX Frontend JavaScript
class ChatApp {
    constructor() {
        this.apiUrl = 'http://localhost:8000';
        this.currentUser = null;
        this.currentChat = null;
        this.token = null;
        this.selectedUsers = new Set();
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.checkAuth();
    }

    setupEventListeners() {
        // Auth forms
        document.getElementById('loginFormElement').addEventListener('submit', (e) => this.handleLogin(e));
        document.getElementById('registerFormElement').addEventListener('submit', (e) => this.handleRegister(e));
        document.getElementById('createChatForm').addEventListener('submit', (e) => this.handleCreateChat(e));
        
        // Message input
        document.getElementById('messageInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });
        
        // Search chats
        document.getElementById('searchChats').addEventListener('input', (e) => this.searchChats(e.target.value));
    }

    checkAuth() {
        const token = localStorage.getItem('xchat_token');
        const user = localStorage.getItem('xchat_user');
        
        if (token && user) {
            this.token = token;
            this.currentUser = JSON.parse(user);
            this.showChatApp();
            this.loadChats();
        }
    }

    // Authentication Methods
    async handleLogin(e) {
        e.preventDefault();
        
        const username = document.getElementById('loginUsername').value;
        const password = document.getElementById('loginPassword').value;
        
        this.showLoading();
        
        try {
            const response = await fetch(`${this.apiUrl}/api/v1/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ username, password })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.token = data.token;
                this.currentUser = {
                    id: data.user_id,
                    username: data.username
                };
                
                localStorage.setItem('xchat_token', this.token);
                localStorage.setItem('xchat_user', JSON.stringify(this.currentUser));
                
                this.showToast('Login successful!', 'success');
                this.showChatApp();
                this.loadChats();
            } else {
                this.showToast(data.detail || 'Login failed', 'error');
            }
        } catch (error) {
            this.showToast('Network error. Please try again.', 'error');
        }
        
        this.hideLoading();
    }

    async handleRegister(e) {
        e.preventDefault();
        
        const username = document.getElementById('regUsername').value;
        const email = document.getElementById('regEmail').value;
        const firstName = document.getElementById('regFirstName').value;
        const lastName = document.getElementById('regLastName').value;
        const password = document.getElementById('regPassword').value;
        
        this.showLoading();
        
        try {
            const response = await fetch(`${this.apiUrl}/api/v1/auth/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    username,
                    email,
                    first_name: firstName,
                    last_name: lastName,
                    password
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.token = data.token;
                this.currentUser = {
                    id: data.user_id,
                    username: data.username
                };
                
                localStorage.setItem('xchat_token', this.token);
                localStorage.setItem('xchat_user', JSON.stringify(this.currentUser));
                
                this.showToast('Registration successful!', 'success');
                this.showChatApp();
                this.loadChats();
            } else {
                this.showToast(data.detail || 'Registration failed', 'error');
            }
        } catch (error) {
            this.showToast('Network error. Please try again.', 'error');
        }
        
        this.hideLoading();
    }

    logout() {
        localStorage.removeItem('xchat_token');
        localStorage.removeItem('xchat_user');
        this.token = null;
        this.currentUser = null;
        this.currentChat = null;
        
        document.getElementById('authModal').classList.add('active');
        document.getElementById('chatApp').classList.remove('active');
        
        this.showToast('Logged out successfully', 'success');
    }

    // UI Methods
    showLogin() {
        document.getElementById('loginForm').classList.add('active');
        document.getElementById('registerForm').classList.remove('active');
    }

    showRegister() {
        document.getElementById('registerForm').classList.add('active');
        document.getElementById('loginForm').classList.remove('active');
    }

    showChatApp() {
        document.getElementById('authModal').classList.remove('active');
        document.getElementById('chatApp').classList.add('active');
        document.getElementById('currentUserName').textContent = this.currentUser.username;
    }

    showLoading() {
        document.getElementById('loadingSpinner').classList.add('active');
    }

    hideLoading() {
        document.getElementById('loadingSpinner').classList.remove('active');
    }

    showToast(message, type = 'info') {
        const toastContainer = document.getElementById('toastContainer');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        const icon = type === 'success' ? 'check-circle' : 
                    type === 'error' ? 'exclamation-circle' : 
                    type === 'warning' ? 'exclamation-triangle' : 'info-circle';
        
        toast.innerHTML = `
            <i class="fas fa-${icon}"></i>
            <span>${message}</span>
        `;
        
        toastContainer.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, 5000);
    }

    // Chat Methods
    async loadChats() {
        try {
            const response = await fetch(`${this.apiUrl}/api/v1/chats`);
            const data = await response.json();
            
            if (response.ok) {
                this.renderChats(data.chats);
            }
        } catch (error) {
            this.showToast('Failed to load chats', 'error');
        }
    }

    renderChats(chats) {
        const chatList = document.getElementById('chatList');
        
        if (chats.length === 0) {
            chatList.innerHTML = `
                <div style="padding: 2rem; text-align: center; color: var(--text-muted);">
                    <i class="fas fa-comments" style="font-size: 2rem; margin-bottom: 1rem;"></i>
                    <p>No chats yet. Create your first chat!</p>
                </div>
            `;
            return;
        }
        
        chatList.innerHTML = chats.map(chat => `
            <div class="chat-item" onclick="app.selectChat('${chat.id}')">
                <div class="avatar">
                    <i class="fas fa-users"></i>
                </div>
                <div class="chat-info">
                    <h4>${chat.name}</h4>
                    <p>${chat.participants.length} participants • ${chat.message_count} messages</p>
                </div>
            </div>
        `).join('');
    }

    async selectChat(chatId) {
        this.currentChat = chatId;
        
        // Update UI
        document.querySelectorAll('.chat-item').forEach(item => item.classList.remove('active'));
        event.currentTarget.classList.add('active');
        
        document.getElementById('welcomeScreen').style.display = 'none';
        document.getElementById('chatContainer').style.display = 'flex';
        
        // Load chat details and messages
        await this.loadChatDetails(chatId);
        await this.loadMessages(chatId);
    }

    async loadChatDetails(chatId) {
        try {
            const response = await fetch(`${this.apiUrl}/api/v1/chats/${chatId}`);
            const data = await response.json();
            
            if (response.ok) {
                document.getElementById('currentChatName').textContent = data.chat.name;
                document.getElementById('chatParticipants').textContent = `${data.chat.participants.length} participants`;
            }
        } catch (error) {
            console.error('Failed to load chat details:', error);
        }
    }

    async loadMessages(chatId) {
        try {
            const response = await fetch(`${this.apiUrl}/api/v1/messages/${chatId}`);
            const data = await response.json();
            
            if (response.ok) {
                this.renderMessages(data.messages);
            }
        } catch (error) {
            console.error('Failed to load messages:', error);
        }
    }

    renderMessages(messages) {
        const container = document.getElementById('messagesContainer');
        
        if (messages.length === 0) {
            container.innerHTML = `
                <div style="text-align: center; color: var(--text-muted); padding: 2rem;">
                    <i class="fas fa-comment" style="font-size: 2rem; margin-bottom: 1rem;"></i>
                    <p>No messages yet. Start the conversation!</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = messages.map(message => {
            const isSent = message.sender_id === this.currentUser.id;
            const time = new Date(message.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
            
            return `
                <div class="message ${isSent ? 'sent' : ''}">
                    <div class="avatar">
                        <i class="fas fa-user"></i>
                    </div>
                    <div>
                        <div class="message-content">
                            ${message.content}
                        </div>
                        <div class="message-info">
                            ${time}
                        </div>
                    </div>
                </div>
            `;
        }).join('');
        
        // Scroll to bottom
        container.scrollTop = container.scrollHeight;
    }

    async sendMessage() {
        const input = document.getElementById('messageInput');
        const content = input.value.trim();
        
        if (!content || !this.currentChat) return;
        
        try {
            const response = await fetch(`${this.apiUrl}/api/v1/messages`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    chat_id: this.currentChat,
                    content: content,
                    sender_id: this.currentUser.id
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                input.value = '';
                await this.loadMessages(this.currentChat);
            } else {
                this.showToast('Failed to send message', 'error');
            }
        } catch (error) {
            this.showToast('Network error. Message not sent.', 'error');
        }
    }

    // Create Chat Methods
    async showCreateChat() {
        document.getElementById('createChatModal').classList.add('active');
        await this.loadUsers();
    }

    closeCreateChat() {
        document.getElementById('createChatModal').classList.remove('active');
        this.selectedUsers.clear();
        document.getElementById('chatName').value = '';
    }

    async loadUsers() {
        try {
            const response = await fetch(`${this.apiUrl}/api/v1/users`);
            const data = await response.json();
            
            if (response.ok) {
                this.renderUsers(data.users);
            }
        } catch (error) {
            this.showToast('Failed to load users', 'error');
        }
    }

    renderUsers(users) {
        const usersList = document.getElementById('usersList');
        
        const filteredUsers = users.filter(user => user.id !== this.currentUser.id);
        
        usersList.innerHTML = filteredUsers.map(user => `
            <div class="user-item" onclick="app.toggleUser('${user.id}')">
                <div class="avatar">
                    <i class="fas fa-user"></i>
                </div>
                <div>
                    <h4>${user.username}</h4>
                    <p>${user.first_name} ${user.last_name}</p>
                </div>
            </div>
        `).join('');
    }

    toggleUser(userId) {
        const userItem = event.currentTarget;
        
        if (this.selectedUsers.has(userId)) {
            this.selectedUsers.delete(userId);
            userItem.classList.remove('selected');
        } else {
            this.selectedUsers.add(userId);
            userItem.classList.add('selected');
        }
    }

    async handleCreateChat(e) {
        e.preventDefault();
        
        const chatName = document.getElementById('chatName').value.trim();
        
        if (!chatName) {
            this.showToast('Please enter a chat name', 'warning');
            return;
        }
        
        if (this.selectedUsers.size === 0) {
            this.showToast('Please select at least one participant', 'warning');
            return;
        }
        
        const participants = [this.currentUser.id, ...Array.from(this.selectedUsers)];
        
        try {
            const response = await fetch(`${this.apiUrl}/api/v1/chats`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    name: chatName,
                    participants: participants
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.showToast('Chat created successfully!', 'success');
                this.closeCreateChat();
                await this.loadChats();
            } else {
                this.showToast(data.detail || 'Failed to create chat', 'error');
            }
        } catch (error) {
            this.showToast('Network error. Please try again.', 'error');
        }
    }

    searchChats(query) {
        const chatItems = document.querySelectorAll('.chat-item');
        
        chatItems.forEach(item => {
            const chatName = item.querySelector('h4').textContent.toLowerCase();
            if (chatName.includes(query.toLowerCase())) {
                item.style.display = 'flex';
            } else {
                item.style.display = 'none';
            }
        });
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new ChatApp();
});

// Global functions for onclick handlers
function showLogin() {
    app.showLogin();
}

function showRegister() {
    app.showRegister();
}

function showCreateChat() {
    app.showCreateChat();
}

function closeCreateChat() {
    app.closeCreateChat();
}

function logout() {
    app.logout();
}

function sendMessage() {
    app.sendMessage();
}