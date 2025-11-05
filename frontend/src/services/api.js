import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
})

// Attach token if present
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('chatx_token')
  if (token) {
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Global response handler for 401
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response && err.response.status === 401) {
      // Clear token and reload to force login (AuthContext will handle redirection)
      localStorage.removeItem('chatx_token')
      localStorage.removeItem('chatx_user')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

// API Service with all endpoints
export const apiService = {
  // Auth endpoints
  auth: {
    register: (data) => api.post('/api/v1/auth/register', data),
    login: (data) => api.post('/api/v1/auth/login', data),
    logout: () => api.post('/api/v1/auth/logout'),
    refresh: (refreshToken) => api.post('/api/v1/auth/refresh', { refresh_token: refreshToken }),
    getMe: () => api.get('/api/v1/auth/me'),
    verifyToken: (token) => api.post('/api/v1/auth/verify-token', { token }),
  },

  // User management endpoints
  users: {
    getProfile: () => api.get('/api/v1/users/profile'),
    updateProfile: (data) => api.put('/api/v1/users/profile', data),
    updateStatus: (status) => api.put('/api/v1/users/status', { status }),
    changePassword: (data) => api.post('/api/v1/users/change-password', data),
    searchUsers: (query, page = 1, limit = 20) => api.get(`/api/v1/users/search?q=${query}&page=${page}&limit=${limit}`),
    getUserById: (userId) => api.get(`/api/v1/users/${userId}`),
    getOnlineUsers: () => api.get('/api/v1/users/online'),
  },

  // Friend management endpoints
  friends: {
    getFriendsList: () => api.get('/api/v1/users/friends/list'),
    sendFriendRequest: (userId) => api.post('/api/v1/users/friends/request', { user_id: userId }),
    getReceivedRequests: () => api.get('/api/v1/users/friends/requests/received'),
    getSentRequests: () => api.get('/api/v1/users/friends/requests/sent'),
    respondToRequest: (requestId, action) => api.post(`/api/v1/users/friends/requests/${requestId}/action`, { action }),
    cancelRequest: (requestId) => api.delete(`/api/v1/users/friends/requests/${requestId}`),
    removeFriend: (friendId) => api.delete(`/api/v1/users/friends/${friendId}`),
  },

  // Block management endpoints
  blocking: {
    blockUser: (userId) => api.post(`/api/v1/users/block/${userId}`),
    unblockUser: (userId) => api.delete(`/api/v1/users/block/${userId}`),
    getBlockedUsers: () => api.get('/api/v1/users/blocked/list'),
  },

  // Chat management endpoints
  chats: {
    getChats: (page = 1, limit = 20) => api.get(`/api/v1/chats?page=${page}&limit=${limit}`),
    createChat: (data) => api.post('/api/v1/chats', data),
    getChatById: (chatId) => api.get(`/api/v1/chats/${chatId}`),
    updateChat: (chatId, data) => api.put(`/api/v1/chats/${chatId}`, data),
    addParticipant: (chatId, userId) => api.post(`/api/v1/chats/${chatId}/participants`, { user_id: userId }),
    removeParticipant: (chatId, userId) => api.delete(`/api/v1/chats/${chatId}/participants/${userId}`),
    updateParticipant: (chatId, userId, data) => api.put(`/api/v1/chats/${chatId}/participants/${userId}`, data),
    archiveChat: (chatId) => api.post(`/api/v1/chats/${chatId}/archive`),
    unarchiveChat: (chatId) => api.delete(`/api/v1/chats/${chatId}/archive`),
  },

  // Messages endpoints (assuming they exist based on chat functionality)
  messages: {
    getMessages: (chatId, page = 1, limit = 50) => api.get(`/api/v1/messages/${chatId}?page=${page}&limit=${limit}`),
    sendMessage: (data) => api.post('/api/v1/messages/send', data),
    uploadMedia: (chatId, formData) => api.post(`/api/v1/messages/upload/${chatId}`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }),
    editMessage: (messageId, content) => api.put(`/api/v1/messages/${messageId}`, { content }),
    deleteMessage: (messageId) => api.delete(`/api/v1/messages/${messageId}`),
    markAsRead: (chatId) => api.post(`/api/v1/messages/${chatId}/read`),
  }
}

export default api
