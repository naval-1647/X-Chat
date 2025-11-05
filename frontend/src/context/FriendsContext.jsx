import React, { createContext, useContext, useState, useEffect } from 'react'
import { useAuth } from './AuthContext'
import { apiService } from '../services/api'

const FriendsContext = createContext(null)
export const useFriends = () => useContext(FriendsContext)

export const FriendsProvider = ({ children }) => {
  const { user, token } = useAuth()
  const [friends, setFriends] = useState([])
  const [receivedRequests, setReceivedRequests] = useState([])
  const [sentRequests, setSentRequests] = useState([])
  const [blockedUsers, setBlockedUsers] = useState([])
  const [onlineUsers, setOnlineUsers] = useState([])
  const [loading, setLoading] = useState(false)

  // Load initial data when user is authenticated
  useEffect(() => {
    if (!user || !token) return
    loadAllData()
  }, [user, token])

  const loadAllData = async () => {
    setLoading(true)
    try {
      // Load data independently so one failure doesn't block others
      await Promise.allSettled([
        loadFriends(),
        loadReceivedRequests(),
        loadSentRequests(),
        loadBlockedUsers(),
        loadOnlineUsers()
      ])
    } catch (err) {
      console.warn('Failed to load friends data', err)
    } finally {
      setLoading(false)
    }
  }

  const loadFriends = async () => {
    try {
      const res = await apiService.friends.getFriendsList()
      setFriends(res.data)
    } catch (err) {
      if (err.response?.status === 404) {
        console.log('Friends endpoint not available')
        setFriends([])
      } else {
        console.warn('Failed to load friends', err)
      }
    }
  }

  const loadReceivedRequests = async () => {
    try {
      const res = await apiService.friends.getReceivedRequests()
      setReceivedRequests(res.data)
    } catch (err) {
      if (err.response?.status === 404) {
        console.log('Friend requests endpoint not available')
        setReceivedRequests([])
      } else {
        console.warn('Failed to load received requests', err)
      }
    }
  }

  const loadSentRequests = async () => {
    try {
      const res = await apiService.friends.getSentRequests()
      setSentRequests(res.data)
    } catch (err) {
      if (err.response?.status === 404) {
        console.log('Sent requests endpoint not available')
        setSentRequests([])
      } else {
        console.warn('Failed to load sent requests', err)
      }
    }
  }

  const loadBlockedUsers = async () => {
    try {
      const res = await apiService.blocking.getBlockedUsers()
      setBlockedUsers(res.data)
    } catch (err) {
      if (err.response?.status === 404) {
        console.log('Blocked users endpoint not available')
        setBlockedUsers([])
      } else {
        console.warn('Failed to load blocked users', err)
      }
    }
  }

  const loadOnlineUsers = async () => {
    try {
      const res = await apiService.users.getOnlineUsers()
      setOnlineUsers(res.data)
    } catch (err) {
      if (err.response?.status === 404) {
        console.log('Online users endpoint not available')
        setOnlineUsers([]) // Set empty array for missing endpoint
      } else {
        console.warn('Failed to load online users', err)
      }
    }
  }

  const sendFriendRequest = async (userId) => {
    try {
      await apiService.friends.sendFriendRequest(userId)
      await loadSentRequests()
      return { success: true }
    } catch (err) {
      return { success: false, error: err.response?.data?.detail || 'Failed to send friend request' }
    }
  }

  const respondToFriendRequest = async (requestId, action) => {
    try {
      await apiService.friends.respondToRequest(requestId, action)
      await Promise.all([loadReceivedRequests(), loadFriends()])
      return { success: true }
    } catch (err) {
      return { success: false, error: err.response?.data?.detail || 'Failed to respond to request' }
    }
  }

  const cancelFriendRequest = async (requestId) => {
    try {
      await apiService.friends.cancelRequest(requestId)
      await loadSentRequests()
      return { success: true }
    } catch (err) {
      return { success: false, error: err.response?.data?.detail || 'Failed to cancel request' }
    }
  }

  const removeFriend = async (friendId) => {
    try {
      await apiService.friends.removeFriend(friendId)
      await loadFriends()
      return { success: true }
    } catch (err) {
      return { success: false, error: err.response?.data?.detail || 'Failed to remove friend' }
    }
  }

  const blockUser = async (userId) => {
    try {
      await apiService.blocking.blockUser(userId)
      await Promise.all([loadBlockedUsers(), loadFriends()])
      return { success: true }
    } catch (err) {
      return { success: false, error: err.response?.data?.detail || 'Failed to block user' }
    }
  }

  const unblockUser = async (userId) => {
    try {
      await apiService.blocking.unblockUser(userId)
      await loadBlockedUsers()
      return { success: true }
    } catch (err) {
      return { success: false, error: err.response?.data?.detail || 'Failed to unblock user' }
    }
  }

  const searchUsers = async (query) => {
    try {
      const res = await apiService.users.searchUsers(query)
      return { success: true, data: res.data }
    } catch (err) {
      return { success: false, error: err.response?.data?.detail || 'Failed to search users' }
    }
  }

  const value = {
    friends,
    receivedRequests,
    sentRequests,
    blockedUsers,
    onlineUsers,
    loading,
    sendFriendRequest,
    respondToFriendRequest,
    cancelFriendRequest,
    removeFriend,
    blockUser,
    unblockUser,
    searchUsers,
    refreshData: loadAllData,
  }

  return <FriendsContext.Provider value={value}>{children}</FriendsContext.Provider>
}