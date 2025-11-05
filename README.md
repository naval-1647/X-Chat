# ChatX API - Real-Time Messaging Backend

## 🚀 Overview

ChatX is a comprehensive real-time messaging backend built with FastAPI, MongoDB, and Redis. It provides a complete solution for building modern chat applications with features like private/group messaging, real-time notifications, user management, and more.

## 🧰 Tech Stack

- **FastAPI** - Modern, fast web framework for building APIs
- **MongoDB** - Document-based database for flexible data storage
- **Redis** - In-memory data store for caching and pub/sub messaging
- **Motor/Beanie** - Async MongoDB ODM
- **JWT** - JSON Web Tokens for authentication
- **WebSocket** - Real-time bi-directional communication
- **Docker** - Containerization for easy deployment

## ✨ Features

### 👤 User Management
- User registration and authentication (JWT)
- Password hashing and security
- User profiles with avatars and status
- Friend requests and contacts management
- User blocking/unblocking
- Online presence tracking

### 💬 Chat System
- Private (1-to-1) messaging
- Group chat with admin controls
- Chat room creation and management
- Participant management (add/remove/mute)
- Chat archiving and pinning

### ✉️ Messaging
- Text message sending/receiving
- Media attachments (images, videos, files)
- Message reactions and emoji support
- Message editing and deletion
- Reply/forward messages
- Typing indicators
- Read receipts and delivery status
- Message history with pagination

### 🔔 Notifications
- Real-time push notifications
- Message notifications
- Friend request notifications
- Mention notifications (@username)
- Unread message counts

### 🛡️ Security & Privacy
- JWT-based authentication
- Password hashing with bcrypt
- Rate limiting for API protection
- User blocking and privacy controls
- Secure file upload validation

### ⚙️ Admin Features
- Admin dashboard APIs
- User management (ban/unban/verify)
- Chat analytics and statistics
- System monitoring and health checks

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- MongoDB 7.0+
- Redis 7.0+
- Docker (optional)

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd chatX
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup environment variables**
   ```bash
   cp .env.example app/.env
   # Edit app/.env with your configuration
   ```

5. **Start MongoDB and Redis**
   ```bash
   # Using Docker
   docker run -d --name mongodb -p 27017:27017 mongo:7
   docker run -d --name redis -p 6379:6379 redis:7-alpine
   ```

6. **Run the application**
   ```bash
   cd app
   python -m app
   ```

7. **Access the API**
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

### Docker Deployment

1. **Development with Docker Compose**
   ```bash
   docker-compose up -d
   ```

2. **Production Deployment**
   ```bash
   # Copy and edit environment file
   cp .env.example .env.prod
   
   # Start production stack
   docker-compose -f docker-compose.prod.yml up -d
   ```

## 📁 Project Structure

```
chatX/
├── app/
│   ├── __init__.py              # FastAPI app initialization
│   ├── __main__.py              # Application entry point
│   ├── config.py                # Configuration settings
│   ├── .env                     # Environment variables
│   ├── database/
│   │   ├── __init__.py
│   │   ├── init_db.py           # Database initialization
│   │   ├── schemas/             # Pydantic models
│   │   │   ├── __init__.py      # Database models
│   │   │   └── models.py        # Request/Response models
│   │   └── repositories/        # Data access layer
│   │       ├── __init__.py
│   │       ├── base.py          # Base repository
│   │       ├── user_repository.py
│   │       ├── chat_repository.py
│   │       ├── message_repository.py
│   │       ├── notification_repository.py
│   │       └── friend_request_repository.py
│   ├── routes/                  # API routes
│   │   ├── __init__.py
│   │   ├── auth.py             # Authentication endpoints
│   │   ├── users.py            # User management endpoints
│   │   └── chats.py            # Chat management endpoints
│   └── utils/                   # Utility functions
│       ├── __init__.py
│       ├── auth.py             # Authentication utilities
│       └── dependencies.py     # FastAPI dependencies
├── requirements.txt             # Python dependencies
├── Dockerfile                  # Docker configuration
├── docker-compose.yml         # Development Docker Compose
├── docker-compose.prod.yml    # Production Docker Compose
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore rules
└── README.md                  # This file
```

## 🔧 Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# Application
APP_NAME=ChatX API
DEBUG=True
HOST=0.0.0.0
PORT=8000

# Database
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=chatx_db

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_URI=redis://localhost:6379

# Security
JWT_SECRET_KEY=your-secret-key
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Admin
ADMIN_EMAIL=admin@chatx.com
ADMIN_USERNAME=admin
ADMIN_PASSWORD=change-this-password

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```

## 📖 API Documentation

Once the application is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Main API Endpoints

#### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Refresh access token
- `GET /api/v1/auth/me` - Get current user profile

#### User Management
- `GET /api/v1/users/profile` - Get user profile
- `PUT /api/v1/users/profile` - Update user profile
- `POST /api/v1/users/friends/request` - Send friend request
- `GET /api/v1/users/friends/list` - Get friends list
- `POST /api/v1/users/block/{user_id}` - Block user

#### Chat Management
- `POST /api/v1/chats/` - Create new chat
- `GET /api/v1/chats/` - Get user's chats
- `GET /api/v1/chats/{chat_id}` - Get specific chat
- `PUT /api/v1/chats/{chat_id}` - Update chat information
- `POST /api/v1/chats/{chat_id}/participants` - Add participants

## 🐳 Docker Support

### Development
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f chatx-api

# Stop services
docker-compose down
```

### Production
```bash
# Start production stack
docker-compose -f docker-compose.prod.yml up -d

# Scale API instances
docker-compose -f docker-compose.prod.yml up -d --scale chatx-api=3
```

## 🔍 Monitoring

The application includes health check endpoints:

- `/health` - Basic health check
- `/health/detailed` - Detailed health with database status

## 🧪 Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest

# Run with coverage
pytest --cov=app
```

## 🚀 Deployment

### Production Checklist

1. **Security**
   - [ ] Change default JWT secret key
   - [ ] Change default admin password
   - [ ] Update CORS origins
   - [ ] Enable HTTPS
   - [ ] Set secure database passwords

2. **Performance**
   - [ ] Configure MongoDB replica set
   - [ ] Set up Redis clustering
   - [ ] Configure reverse proxy (Nginx)
   - [ ] Enable API rate limiting

3. **Monitoring**
   - [ ] Set up application logging
   - [ ] Configure health checks
   - [ ] Set up monitoring (Prometheus/Grafana)
   - [ ] Configure alerting

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

For support and questions:
- Create an issue in the GitHub repository
- Email: support@chatx.com
- Documentation: http://localhost:8000/docs

## 🔄 Roadmap

### Upcoming Features
- [ ] End-to-end encryption
- [ ] Voice messages
- [ ] Video calling
- [ ] Message scheduling
- [ ] Chat themes
- [ ] File sharing with cloud storage
- [ ] Advanced admin analytics
- [ ] Multi-language support
- [ ] Mobile push notifications (FCM)
- [ ] Chatbot integration

---

**Made with ❤️ using FastAPI, MongoDB, and Redis**