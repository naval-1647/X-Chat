import React from 'react'
import { useChat } from '../context/ChatContext'
import { useAuth } from '../context/AuthContext'

export default function ChatList() {
  const { chats, fetchMessages, setCurrentChat, onlineUsers } = useChat()
  const { user } = useAuth()

  const getChatDisplayName = (chat) => {
    // For group chats, use the chat name or a default
    if (chat.type === 'group') {
      return chat.name || 'Group Chat'
    }
    
    // For private/direct chats, show the other participant's name
    if (chat.type === 'private' || chat.type === 'direct') {
      if (chat.participants && chat.participants.length >= 2) {
        // Find the other participant (not the current user)
        const otherParticipant = chat.participants.find(p => p.user_id !== user?.id)
        if (otherParticipant) {
          return otherParticipant.full_name || otherParticipant.username
        }
      }
    }
    
    // Fallback to chat name, title, or ID
    return chat.name || chat.title || `Chat ${chat.id.slice(-8)}`
  }

  const getOnlineStatus = (chat) => {
    // For private chats, check if the other participant is online
    if (chat.type === 'private' || chat.type === 'direct') {
      if (chat.participants && chat.participants.length >= 2) {
        const otherParticipant = chat.participants.find(p => p.user_id !== user?.id)
        if (otherParticipant && onlineUsers && onlineUsers.has(otherParticipant.user_id)) {
          return '●'
        }
      }
    }
    return ''
  }

  return (
    <div className="p-2">
      <h3 className="px-2 py-3 font-semibold">Chats</h3>
      <ul>
        {chats && chats.length ? (
          chats.map((c) => (
            <li key={c.id} className="p-2 hover:bg-gray-50 cursor-pointer flex justify-between items-center" onClick={() => { setCurrentChat(c.id); fetchMessages(c.id) }}>
              <div className="flex-1">
                <div className="font-medium">{getChatDisplayName(c)}</div>
                <div className="text-xs text-gray-500">{c.last_message?.content || 'No messages yet'}</div>
              </div>
              <div className="text-xs text-green-500">{getOnlineStatus(c)}</div>
            </li>
          ))
        ) : (
          <li className="p-2 text-gray-500">No chats yet</li>
        )}
      </ul>
    </div>
  )
}
