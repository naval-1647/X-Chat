import React, { useState } from 'react'
import { useFriends } from '../context/FriendsContext'
import { useChat } from '../context/ChatContext'

export default function FriendsPage() {
  const { 
    friends, 
    receivedRequests, 
    sentRequests, 
    blockedUsers,
    onlineUsers,
    sendFriendRequest,
    respondToFriendRequest,
    cancelFriendRequest,
    removeFriend,
    blockUser,
    unblockUser,
    searchUsers,
    loading 
  } = useFriends()
  
  const { createChat } = useChat()
  const [activeTab, setActiveTab] = useState('friends')
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [searching, setSearching] = useState(false)

  const handleSearch = async (e) => {
    e.preventDefault()
    if (!searchQuery.trim()) return
    
    setSearching(true)
    const result = await searchUsers(searchQuery)
    if (result.success) {
      setSearchResults(result.data?.items || result.data || [])
    }
    setSearching(false)
  }

  const handleSendRequest = async (userId) => {
    const result = await sendFriendRequest(userId)
    if (result.success) {
      // Remove from search results or update UI
      setSearchResults(prev => prev.filter(user => user.id !== userId))
    }
  }

  const handleStartChat = async (friendId) => {
    const result = await createChat([friendId], 'direct')
    if (result.success) {
      // Chat created successfully, navigate or update UI
      console.log('Chat created:', result.data)
    }
  }

  const tabs = [
    { id: 'friends', label: 'Friends', count: friends.length },
    { id: 'received', label: 'Requests', count: receivedRequests.length },
    { id: 'sent', label: 'Sent', count: sentRequests.length },
    { id: 'blocked', label: 'Blocked', count: blockedUsers.length },
    { id: 'search', label: 'Search', count: null },
  ]

  if (loading) {
    return <div className="p-4">Loading friends...</div>
  }

  return (
    <div className="max-w-4xl mx-auto p-4">
      <h1 className="text-2xl font-bold mb-6">Friends & Social</h1>
      
      {/* Tabs */}
      <div className="border-b mb-6">
        <div className="flex space-x-4">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`pb-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab.label} {tab.count !== null && <span className="bg-gray-200 px-2 py-1 rounded-full text-xs ml-1">{tab.count}</span>}
            </button>
          ))}
        </div>
      </div>

      {/* Content based on active tab */}
      {activeTab === 'friends' && (
        <div>
          <h2 className="text-lg font-semibold mb-4">Friends ({friends.length})</h2>
          <div className="grid gap-4">
            {friends.map(friend => (
              <div key={friend.id} className="flex items-center justify-between p-4 bg-white rounded shadow">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-gray-300 rounded-full flex items-center justify-center">
                    {friend.username[0].toUpperCase()}
                  </div>
                  <div>
                    <div className="font-medium">{friend.username}</div>
                    <div className="text-xs text-gray-500">
                      {onlineUsers.some(u => u.id === friend.id) ? (
                        <span className="text-green-500">● Online</span>
                      ) : (
                        <span className="text-gray-400">○ Offline</span>
                      )}
                    </div>
                  </div>
                </div>
                <div className="flex space-x-2">
                  <button
                    onClick={() => handleStartChat(friend.id)}
                    className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
                  >
                    Chat
                  </button>
                  <button
                    onClick={() => removeFriend(friend.id)}
                    className="px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700"
                  >
                    Remove
                  </button>
                </div>
              </div>
            ))}
            {friends.length === 0 && (
              <div className="text-center py-8 text-gray-500">No friends yet. Start by searching for users!</div>
            )}
          </div>
        </div>
      )}

      {activeTab === 'received' && (
        <div>
          <h2 className="text-lg font-semibold mb-4">Friend Requests ({receivedRequests.length})</h2>
          <div className="grid gap-4">
            {receivedRequests.map(request => (
              <div key={request.id} className="flex items-center justify-between p-4 bg-white rounded shadow">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-gray-300 rounded-full flex items-center justify-center">
                    {request.from_user?.username[0].toUpperCase()}
                  </div>
                  <div>
                    <div className="font-medium">{request.from_user?.username}</div>
                    <div className="text-xs text-gray-500">Sent {new Date(request.created_at).toLocaleDateString()}</div>
                  </div>
                </div>
                <div className="flex space-x-2">
                  <button
                    onClick={() => respondToFriendRequest(request.id, 'accept')}
                    className="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700"
                  >
                    Accept
                  </button>
                  <button
                    onClick={() => respondToFriendRequest(request.id, 'reject')}
                    className="px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700"
                  >
                    Reject
                  </button>
                </div>
              </div>
            ))}
            {receivedRequests.length === 0 && (
              <div className="text-center py-8 text-gray-500">No pending friend requests</div>
            )}
          </div>
        </div>
      )}

      {activeTab === 'search' && (
        <div>
          <h2 className="text-lg font-semibold mb-4">Search Users</h2>
          <form onSubmit={handleSearch} className="mb-6">
            <div className="flex gap-2">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by username or email..."
                className="flex-1 px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                type="submit"
                disabled={searching}
                className="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
              >
                {searching ? 'Searching...' : 'Search'}
              </button>
            </div>
          </form>

          <div className="grid gap-4">
            {searchResults.map(user => (
              <div key={user.id} className="flex items-center justify-between p-4 bg-white rounded shadow">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-gray-300 rounded-full flex items-center justify-center">
                    {user.username[0].toUpperCase()}
                  </div>
                  <div>
                    <div className="font-medium">{user.username}</div>
                    <div className="text-xs text-gray-500">{user.email}</div>
                  </div>
                </div>
                <div className="flex space-x-2">
                  <button
                    onClick={() => handleSendRequest(user.id)}
                    className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
                  >
                    Add Friend
                  </button>
                  <button
                    onClick={() => blockUser(user.id)}
                    className="px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700"
                  >
                    Block
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}