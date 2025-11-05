import React, { useRef, useEffect } from 'react'
import { useChat } from '../context/ChatContext'
import MessageInput from './MessageInput'
import { useAuth } from '../context/AuthContext'

export default function ChatWindow() {
  const { messages, currentChat, chats } = useChat()
  const { user } = useAuth()
  const ref = useRef(null)

  useEffect(() => {
    if (ref.current) ref.current.scrollTop = ref.current.scrollHeight
  }, [messages])

  const getChatDisplayName = () => {
    const chat = chats.find(c => c.id === currentChat)
    if (!chat) return `Chat ${currentChat?.slice(-8) || ''}`
    
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

  return (
    <div className="flex-1 flex flex-col h-full">
      <div className="p-3 border-b bg-white">
        <div className="font-semibold">{getChatDisplayName()}</div>
      </div>
      <div ref={ref} className="flex-1 overflow-auto p-4 space-y-3">
        {messages && messages.map((m, idx) => {
          const me = m.from === user.id || m.sender_id === user.id || m.user_id === user.id
          return (
            <div key={idx} className={`max-w-md ${me ? 'ml-auto bg-blue-500 text-white' : 'bg-white text-gray-800'} p-3 rounded`}>
              {/* Render different content based on message type */}
              {m.message_type === 'image' && m.media ? (
                <div className="space-y-2">
                  <img 
                    src={`http://localhost:8000${m.media.file_url}`} 
                    alt={m.media.file_name}
                    className="max-w-full h-auto rounded cursor-pointer"
                    onClick={() => window.open(`http://localhost:8000${m.media.file_url}`, '_blank')}
                  />
                  {m.content && <div className="text-sm">{m.content}</div>}
                </div>
              ) : m.message_type === 'video' && m.media ? (
                <div className="space-y-2">
                  <video 
                    controls 
                    className="max-w-full h-auto rounded"
                    preload="metadata"
                  >
                    <source src={`http://localhost:8000${m.media.file_url}`} type={m.media.mime_type} />
                    Your browser does not support the video tag.
                  </video>
                  {m.content && <div className="text-sm">{m.content}</div>}
                </div>
              ) : m.message_type === 'audio' && m.media ? (
                <div className="space-y-2">
                  <audio controls className="w-full">
                    <source src={`http://localhost:8000${m.media.file_url}`} type={m.media.mime_type} />
                    Your browser does not support the audio tag.
                  </audio>
                  {m.content && <div className="text-sm">{m.content}</div>}
                </div>
              ) : m.message_type === 'document' && m.media ? (
                <div className="space-y-2">
                  <div className="bg-gray-100 p-3 rounded-lg max-w-xs">
                    <div className="flex items-center gap-2">
                      <svg className="w-8 h-8 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      <div className="flex-1">
                        <p className="font-medium text-sm truncate" title={m.media.file_name}>
                          {m.media.file_name}
                        </p>
                        {m.media.file_size && (
                          <p className="text-xs text-gray-500">
                            {(m.media.file_size / 1024 / 1024).toFixed(1)} MB
                          </p>
                        )}
                        <a 
                          href={`http://localhost:8000${m.media.file_url}`} 
                          download={m.media.file_name}
                          className="text-blue-500 hover:text-blue-700 text-sm inline-flex items-center gap-1"
                        >
                          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                          </svg>
                          Download
                        </a>
                      </div>
                    </div>
                  </div>
                  {m.content && <div className="text-sm">{m.content}</div>}
                </div>
              ) : (
                <div className="text-sm">{m.content}</div>
              )}
              <div className={`text-xs mt-2 ${me ? 'text-blue-100' : 'text-gray-500'}`}>
                {new Date(m.created_at || Date.now()).toLocaleString()}
              </div>
            </div>
          )
        })}
      </div>

      <div className="p-3 bg-white border-t">
        <MessageInput />
      </div>
    </div>
  )
}
