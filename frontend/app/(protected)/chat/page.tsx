'use client'

import { useState, useRef, useEffect } from 'react'
import { apiPost } from '@/lib/api'
import type { QueryResponse } from '@/lib/types'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { SendHorizontal } from 'lucide-react'
import { cn } from '@/lib/utils'

interface Message {
  role: 'user' | 'assistant' | 'error'
  content: string
}

const WELCOME: Message = {
  role: 'assistant',
  content: "Hi! I'm your finance AI. Ask me anything about your spending — for example, \"How much did I spend on food last month?\"",
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([WELCOME])
  const [threadId, setThreadId] = useState<string | null>(null)
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function sendMessage() {
    const text = input.trim()
    if (!text || loading) return

    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: text }])
    setLoading(true)

    try {
      const body = threadId
        ? { message: text, thread_id: threadId }
        : { message: text }
      const data = await apiPost<QueryResponse>('/query', body)
      setThreadId(data.thread_id)
      setMessages(prev => [...prev, { role: 'assistant', content: data.response }])
    } catch (err) {
      setMessages(prev => [
        ...prev,
        {
          role: 'error',
          content: err instanceof Error ? err.message : 'Something went wrong. Please try again.',
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-7rem)]">
      <div className="flex-1 overflow-y-auto space-y-4 pb-4">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={cn('flex gap-3', msg.role === 'user' ? 'justify-end' : 'justify-start')}
          >
            {msg.role !== 'user' && (
              <div className="w-8 h-8 rounded-full bg-indigo-500 flex items-center justify-center text-sm flex-shrink-0 mt-0.5">
                🤖
              </div>
            )}
            <div
              className={cn(
                'max-w-[75%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed',
                msg.role === 'user'
                  ? 'bg-indigo-500 text-white rounded-tr-sm'
                  : msg.role === 'error'
                  ? 'bg-red-50 border border-red-200 text-red-700 rounded-tl-sm'
                  : 'bg-white border border-indigo-200 text-gray-800 rounded-tl-sm'
              )}
            >
              {msg.content}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex gap-3 justify-start">
            <div className="w-8 h-8 rounded-full bg-indigo-200 flex items-center justify-center text-sm flex-shrink-0">
              🤖
            </div>
            <div className="bg-white border border-indigo-200 rounded-2xl rounded-tl-sm px-4 py-3">
              <div className="flex gap-1 items-center">
                <span className="w-1.5 h-1.5 bg-indigo-300 rounded-full animate-bounce [animation-delay:0ms]" />
                <span className="w-1.5 h-1.5 bg-indigo-300 rounded-full animate-bounce [animation-delay:150ms]" />
                <span className="w-1.5 h-1.5 bg-indigo-300 rounded-full animate-bounce [animation-delay:300ms]" />
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      <div className="flex gap-2 pt-4 border-t border-indigo-100">
        <Input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about your finances…"
          disabled={loading}
          className="flex-1 rounded-full border-indigo-200 bg-white focus-visible:ring-indigo-400 px-5"
        />
        <Button
          onClick={sendMessage}
          disabled={loading || !input.trim()}
          size="icon"
          className="rounded-full bg-indigo-500 hover:bg-indigo-600 text-white w-10 h-10 flex-shrink-0"
        >
          <SendHorizontal className="w-4 h-4" />
        </Button>
      </div>
    </div>
  )
}
