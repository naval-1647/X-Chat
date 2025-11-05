import React from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import './index.css'
import { AuthProvider } from './context/AuthContext'
import { ChatProvider } from './context/ChatContext'
import { FriendsProvider } from './context/FriendsContext'

createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter
      future={{
        v7_startTransition: true,
        v7_relativeSplatPath: true
      }}
    >
      <AuthProvider>
        <FriendsProvider>
          <ChatProvider>
            <App />
          </ChatProvider>
        </FriendsProvider>
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>
)
