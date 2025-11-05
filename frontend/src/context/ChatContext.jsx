import React, { createContext, useContext, useEffect, useState, useRef } from 'react'
import { useAuth } from './AuthContext'
import io from 'socket.io-client'
import { apiService } from '../services/api'

const ChatContext = createContext(null)
export const useChat = () => useContext(ChatContext)

export const ChatProvider = ({ children }) => {
  const { user, token } = useAuth()
  const [socket, setSocket] = useState(null)
  const [currentChat, setCurrentChat] = useState(null)
  const [messages, setMessages] = useState([])
  const [chats, setChats] = useState([])
  const [onlineUsers, setOnlineUsers] = useState(new Set())
  const socketRef = useRef(null)

  // Load chats function
  const loadChats = async () => {
    if (!user || !token) return
    try {
      const res = await apiService.chats.getChats()
      setChats(res.data?.items || res.data || [])
    } catch (err) {
      console.warn('Failed to load chats', err)
    }
  }

  useEffect(() => {
    // Load chats only when user is authenticated
    loadChats()
  }, [user, token])

  useEffect(() => {
    if (!user || !token) return

    // WebSocket connection disabled until backend implements it
    console.log('WebSocket connection disabled - using REST API fallback only')
    
    // TODO: Enable when backend implements WebSocket support
    // try {
    //   const s = io('http://localhost:8000', {
    //     path: '/socket.io',
    //     transports: ['websocket'],
    //     auth: { token },
    //     reconnectionAttempts: 5,
    //   })
    //   socketRef.current = s
    //   setSocket(s)
    //   // ... socket event handlers
    // } catch (err) {
    //   console.warn('Socket.io failed, no real-time features available', err)
    // }
  }, [user, token])

  const fetchMessages = async (chatId) => {
    try {
      const res = await apiService.messages.getMessages(chatId)
      setMessages(res.data?.items || res.data || [])
      setCurrentChat(chatId)
    } catch (err) {
      console.warn('Failed to fetch messages', err)
    }
  }

  const sendMessage = async (chatId, content) => {
    try {
      // Use REST API since WebSocket is not implemented yet
      await apiService.messages.sendMessage({ chat_id: chatId, content })
      // Refresh messages after sending
      await fetchMessages(chatId)
    } catch (err) {
      console.error('Failed to send message:', err)
    }
  }

  const createChat = async (participants, chatType = 'direct', title = null) => {
    try {
      const res = await apiService.chats.createChat({
        participants,
        chat_type: chatType,
        title
      })
      await loadChats() // Refresh chat list
      return { success: true, data: res.data }
    } catch (err) {
      return { success: false, error: err.response?.data?.detail || 'Failed to create chat' }
    }
  }

  const value = {
    socket: socketRef.current,
    currentChat,
    setCurrentChat,
    messages,
    fetchMessages,
    sendMessage,
    createChat,
    chats,
    onlineUsers,
    refreshChats: loadChats,
  }

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>
}
