# 🚀 Xchat - Quick Start Guide

## � What is Xchat?
Xchat is a modern, real-time messaging platform with a beautiful UI and powerful backend API.

## 🌐 Live Links
- **Frontend App**: Open `web/index.html` in your browser
- **Demo Page**: Open `web/demo.html` for easy navigation
- **Live API**: https://x-chat-2.onrender.com
- **API Documentation**: https://x-chat-2.onrender.com/docs
- **GitHub Repository**: https://github.com/naval-1647/X-Chat

## 🎯 How to Use

### 1. Quick Start (Recommended)
1. Open `web/demo.html` in your browser
2. Click "Launch App" to open the main application
3. Register a new account or login with existing credentials
4. Start chatting!

### 2. Direct Access
1. Open `web/index.html` in your browser
2. The app will connect to the live API automatically

## ✨ Features

### 🔐 Authentication
- **Register**: Create new account with username/email/password
- **Login**: Secure JWT-based authentication
- **Auto-login**: Remembers your session

### 💬 Messaging
- **Real-time**: Instant message delivery
- **Group Chats**: Create and join group conversations
- **User Management**: Add/remove users from chats
- **Message History**: All messages are stored and retrievable

### 🎨 Beautiful Interface
- **Modern Design**: Dark theme with gradients and animations
- **Responsive**: Works on desktop, tablet, and mobile
- **Intuitive**: Easy-to-use chat interface
- **Modals**: Clean popup forms for actions

## �️ Technical Stack

### Frontend
- **HTML5**: Semantic markup
- **CSS3**: Modern styling with animations
- **JavaScript**: ES6+ with fetch API
- **Font Awesome**: Beautiful icons

### Backend
- **FastAPI**: High-performance Python web framework
- **Pydantic**: Data validation and serialization
- **JWT**: Secure authentication tokens
- **In-memory Storage**: Fast message handling

### Deployment
- **Render**: Cloud platform hosting
- **GitHub**: Version control and collaboration

## 🔧 API Endpoints

### Authentication
- `POST /register` - Create new account
- `POST /login` - User authentication

### User Management
- `GET /users` - List all users
- `GET /users/me` - Get current user info
- `PUT /users/me` - Update user profile

### Chat Management
- `GET /chats` - Get user's chats
- `POST /chats` - Create new chat
- `POST /chats/{chat_id}/users` - Add user to chat
- `DELETE /chats/{chat_id}/users/{user_id}` - Remove user from chat

### Messaging
- `GET /chats/{chat_id}/messages` - Get chat messages
- `POST /chats/{chat_id}/messages` - Send new message

## 🎮 Usage Tips

1. **First Time**: Start with demo.html for easy navigation
2. **Testing**: Use multiple browser tabs to test real-time features
3. **Mobile**: The interface is fully responsive
4. **API**: Check /docs for interactive API testing

## 🐛 Troubleshooting

- **Can't connect**: Check if API is running at https://x-chat-2.onrender.com
- **Login issues**: Make sure to register first
- **Messages not showing**: Refresh the page or check network connection

## � Development

### Local Setup
1. Run the backend: `python simple_app.py`
2. Open `web/index.html` in browser
3. Update API_BASE_URL in script.js if needed

### Deployment
- Backend is deployed on Render
- Frontend can be deployed on any static hosting (Netlify, Vercel, etc.)

## 📞 Support
- Check GitHub issues: https://github.com/naval-1647/X-Chat/issues
- API documentation: https://x-chat-2.onrender.com/docs

---

**Made with ❤️ using FastAPI, HTML, CSS, and JavaScript**