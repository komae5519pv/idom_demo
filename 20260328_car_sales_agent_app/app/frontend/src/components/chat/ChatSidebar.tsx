import { useState, useRef, useEffect } from 'react'
import { FiSend, FiX, FiMessageSquare, FiTrash2 } from 'react-icons/fi'
import { HiOutlineSparkles } from 'react-icons/hi2'
import clsx from 'clsx'
import { useAppStore } from '../../store'
import { chatAPI } from '../../api'
import type { ChatMessage } from '../../types'
import { LoadingSpinner } from '../common/LoadingSpinner'

interface ChatSidebarProps {
  isOpen: boolean
  onToggle: () => void
  customerId?: string
}

export function ChatSidebar({ isOpen, onToggle, customerId }: ChatSidebarProps) {
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const { chatMessages, chatSessionId, addChatMessage, clearChat } = useAppStore()

  useEffect(() => {
    scrollToBottom()
  }, [chatMessages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage: ChatMessage = { role: 'user', content: input.trim() }
    addChatMessage(userMessage)
    setInput('')
    setIsLoading(true)

    try {
      // Use streaming for better UX
      let fullResponse = ''
      const assistantMessage: ChatMessage = { role: 'assistant', content: '' }

      for await (const chunk of chatAPI.sendStream({
        session_id: chatSessionId,
        customer_id: customerId,
        message: userMessage.content,
      })) {
        fullResponse += chunk
        // Update the last message in real-time (we'll add the complete message after)
      }

      assistantMessage.content = fullResponse
      addChatMessage(assistantMessage)
    } catch (error) {
      console.error('Chat error:', error)
      addChatMessage({
        role: 'assistant',
        content: 'エラーが発生しました。もう一度お試しください。',
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleClearChat = () => {
    clearChat()
  }

  // Collapsed state - show toggle button
  if (!isOpen) {
    return (
      <button
        onClick={onToggle}
        className="fixed right-4 bottom-4 w-14 h-14 bg-blue-600 text-white rounded-full shadow-lg hover:bg-blue-700 transition-colors flex items-center justify-center z-50"
      >
        <FiMessageSquare className="w-6 h-6" />
      </button>
    )
  }

  return (
    <div className="w-96 bg-white border-l border-gray-200 flex flex-col animate-slide-in-right">
      {/* Header */}
      <div className="h-16 px-4 flex items-center justify-between border-b border-gray-200">
        <div className="flex items-center gap-2">
          <HiOutlineSparkles className="w-5 h-5 text-purple-500" />
          <h2 className="font-semibold text-gray-900">Ask AI</h2>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={handleClearChat}
            className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            title="履歴をクリア"
          >
            <FiTrash2 className="w-4 h-4" />
          </button>
          <button
            onClick={onToggle}
            className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <FiX className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {chatMessages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center text-gray-500">
            <HiOutlineSparkles className="w-12 h-12 text-gray-300 mb-4" />
            <p className="text-sm">
              車両や顧客について
              <br />
              何でも質問してください
            </p>
          </div>
        ) : (
          chatMessages.map((msg, idx) => (
            <ChatBubble key={idx} message={msg} />
          ))
        )}
        {isLoading && (
          <div className="flex items-center gap-2 text-gray-500">
            <LoadingSpinner size="sm" />
            <span className="text-sm">回答を生成中...</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="p-4 border-t border-gray-200">
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="メッセージを入力..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <FiSend className="w-5 h-5" />
          </button>
        </div>
      </form>
    </div>
  )
}

function ChatBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === 'user'

  return (
    <div
      className={clsx(
        'flex',
        isUser ? 'justify-end' : 'justify-start'
      )}
    >
      <div
        className={clsx(
          'max-w-[85%] px-4 py-2 rounded-2xl text-sm',
          isUser
            ? 'bg-blue-600 text-white rounded-br-md'
            : 'bg-gray-100 text-gray-800 rounded-bl-md'
        )}
      >
        <p className="whitespace-pre-wrap">{message.content}</p>
      </div>
    </div>
  )
}
