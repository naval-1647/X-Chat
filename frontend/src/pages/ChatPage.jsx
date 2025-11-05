import React, { useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import { useChat } from '../context/ChatContext'
import Navbar from '../components/Navbar'
import ChatList from '../components/ChatList'
import ChatWindow from '../components/ChatWindow'

export default function ChatPage() {
  const { user } = useAuth()
  const { chats, currentChat } = useChat()

  useEffect(() => {
    document.title = user ? `${user.username} — ChatX` : 'ChatX'
  }, [user])

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <div className="flex flex-1 overflow-hidden">
        <aside className="w-72 border-r bg-white">
          <ChatList />
        </aside>
        <main className="flex-1 bg-gray-100 p-4 flex flex-col">
          {currentChat ? <ChatWindow /> : <div className="m-auto text-gray-500">Select a chat to start messaging</div>}
        </main>
      </div>
    </div>
  )
}
