# 🚀 Xchat Local Development

## Quick Start

### Option 1: One-Click Start (Recommended)
```bash
# Double-click this file or run in terminal:
start_local.bat
```
This will automatically start both backend and frontend servers.

### Option 2: Manual Start

#### Start Backend (Terminal 1):
```bash
python simple_app.py
```
Backend will run on: http://localhost:8000

#### Start Frontend (Terminal 2):
```bash
python start_frontend.py
```
Frontend will run on: http://localhost:3000

## 🌐 Local URLs

- **Main App**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Start Page**: http://localhost:3000/start.html
- **Demo Page**: http://localhost:3000/demo.html

## 🔧 Development Notes

- Frontend now connects to `http://localhost:8000` instead of remote API
- CORS is properly configured for local development
- All data is stored in memory (resets when backend restarts)
- Hot reload: Just refresh browser for frontend changes

## 📁 File Structure
```
chatX/
├── simple_app.py          # FastAPI backend server
├── start_frontend.py      # Frontend HTTP server
├── start_local.bat        # One-click start script
└── web/
    ├── index.html         # Main chat application
    ├── start.html         # Quick start page
    ├── demo.html          # Demo and navigation
    ├── script.js          # Frontend JavaScript
    └── styles.css         # CSS styles
```

## 🛠️ Features

✅ **Backend API (Port 8000)**
- User registration and authentication
- Real-time messaging endpoints
- Chat management
- User management
- JWT token authentication

✅ **Frontend (Port 3000)**
- Beautiful dark theme interface
- User authentication forms
- Real-time chat interface
- Responsive design
- Local API integration

## 🎯 Testing

1. Open http://localhost:3000
2. Register a new user account
3. Create a chat
4. Send messages
5. Test with multiple browser tabs for real-time features

## 🔄 Switching Back to Remote

To switch back to the remote API, change in `web/script.js`:
```javascript
this.apiUrl = 'https://x-chat-2.onrender.com';
```

---

**Happy coding! 🎉**