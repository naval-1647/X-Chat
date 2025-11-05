import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useFriends } from '../context/FriendsContext'

export default function Navbar() {
  const { user, logout } = useAuth()
  const { receivedRequests } = useFriends()
  const location = useLocation()
  
  const navItems = [
    { path: '/chat', label: 'Chats', icon: '💬' },
    { path: '/friends', label: 'Friends', icon: '👥', badge: receivedRequests.length },
  ]

  return (
    <header className="flex items-center justify-between p-4 bg-white border-b">
      <div className="flex items-center space-x-6">
        <div className="font-bold text-xl">ChatX</div>
        <nav className="flex space-x-4">
          {navItems.map(item => (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center space-x-1 px-3 py-2 rounded transition-colors relative ${
                location.pathname === item.path
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-600 hover:text-gray-800 hover:bg-gray-100'
              }`}
            >
              <span>{item.icon}</span>
              <span>{item.label}</span>
              {item.badge && item.badge > 0 && (
                <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                  {item.badge}
                </span>
              )}
            </Link>
          ))}
        </nav>
      </div>
      
      <div className="flex items-center gap-4">
        {user && (
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center text-sm">
              {user.username[0].toUpperCase()}
            </div>
            <div className="text-sm">{user.username}</div>
          </div>
        )}
        <button onClick={logout} className="text-sm text-red-600 hover:text-red-800">
          Logout
        </button>
      </div>
    </header>
  )
}
