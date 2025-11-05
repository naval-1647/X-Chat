import React, { useState, useRef } from 'react'
import { useChat } from '../context/ChatContext'
import { apiService } from '../services/api'

export default function MessageInput() {
  const [text, setText] = useState('')
  const [uploading, setUploading] = useState(false)
  const [dragOver, setDragOver] = useState(false)
  const { currentChat, sendMessage, fetchMessages } = useChat()
  const fileInputRef = useRef(null)

  const handleSend = (e) => {
    e.preventDefault()
    if (!text.trim() || !currentChat) return
    sendMessage(currentChat, text.trim())
    setText('')
  }

  const handleFileSelect = (e) => {
    const file = e.target.files[0]
    if (file) {
      handleFileUpload(file)
    }
  }

  const handleFileUpload = async (file) => {
    if (!currentChat || uploading) return

    // Check file size (10MB limit)
    const maxSize = 10 * 1024 * 1024 // 10MB
    if (file.size > maxSize) {
      const sizeMB = (file.size / 1024 / 1024).toFixed(1)
      alert(`File "${file.name}" is ${sizeMB}MB. Maximum file size is 10MB.`)
      return
    }

    setUploading(true)
    try {
      // Determine message type based on file type
      const fileType = file.type.toLowerCase()
      let messageType = 'document'
      
      if (fileType.startsWith('image/')) {
        messageType = 'image'
      } else if (fileType.startsWith('video/')) {
        messageType = 'video'
      } else if (fileType.startsWith('audio/')) {
        messageType = 'audio'
      }

      // Create FormData for file upload
      const formData = new FormData()
      formData.append('file', file)
      formData.append('message_type', messageType)
      
      // Add appropriate message content based on type
      const contentMap = {
        'image': '📷 Shared a photo',
        'video': '🎥 Shared a video', 
        'audio': '🎵 Shared an audio file',
        'document': '📄 Shared a document'
      }
      formData.append('content', contentMap[messageType] || 'Shared a file')

      // Upload file
      await apiService.messages.uploadMedia(currentChat, formData)
      
      // Refresh messages after upload
      await fetchMessages(currentChat)
      
    } catch (error) {
      console.error('Failed to upload file:', error)
      const errorMessage = error.response?.data?.detail || 'Failed to upload file. Please try again.'
      alert(errorMessage)
    } finally {
      setUploading(false)
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  const triggerFileSelect = () => {
    fileInputRef.current?.click()
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    setDragOver(true)
  }

  const handleDragLeave = (e) => {
    e.preventDefault()
    setDragOver(false)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragOver(false)
    
    const files = e.dataTransfer.files
    if (files.length > 0) {
      handleFileUpload(files[0])
    }
  }

  return (
    <div className="relative">
      {dragOver && (
        <div className="absolute inset-0 bg-blue-100 bg-opacity-90 border-2 border-dashed border-blue-400 rounded-lg flex items-center justify-center z-10">
          <div className="text-blue-600 text-center">
            <svg className="w-8 h-8 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            <p className="font-medium">Drop files here to upload</p>
            <p className="text-sm text-blue-500">Images, videos, audio, or documents</p>
          </div>
        </div>
      )}
      <div
        className={`flex items-center gap-2 p-4 bg-white border-t transition-colors ${
          dragOver ? 'border-blue-300' : ''
        }`}
        onDragEnter={handleDragOver}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
      >
      <form onSubmit={handleSend} className="flex gap-2 flex-1">
        <input 
          value={text} 
          onChange={(e) => setText(e.target.value)} 
          className="flex-1 p-2 border rounded" 
          placeholder="Type a message..." 
          disabled={uploading}
        />
        <button 
          type="submit" 
          className="px-4 py-2 bg-blue-600 text-white rounded disabled:opacity-50"
          disabled={uploading || !text.trim()}
        >
          Send
        </button>
      </form>
      
      {/* File Upload Button */}
      <button
        type="button"
        onClick={triggerFileSelect}
        disabled={uploading}
        className={`px-3 py-2 rounded transition-colors flex items-center gap-1 ${
          uploading 
            ? 'bg-gray-100 text-gray-400 cursor-not-allowed' 
            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
        }`}
        title={uploading ? 'Uploading...' : 'Upload photo, video, audio, or document (max 10MB)'}
      >
        {uploading ? (
          <>
            <div className="w-4 h-4 border-2 border-gray-400 border-t-transparent rounded-full animate-spin"></div>
            <span className="text-xs">Uploading...</span>
          </>
        ) : (
          <>
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
            </svg>
            <span className="text-xs hidden sm:inline">File</span>
          </>
        )}
      </button>

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        onChange={handleFileSelect}
        accept="image/*,video/*,audio/*,.pdf,.doc,.docx,.txt,.rtf"
        className="hidden"
        disabled={uploading}
      />
      </div>
    </div>
  );
};
