"use client"

import { useState, useRef, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { toast, ToastContainer } from "react-toastify"
import "react-toastify/dist/ReactToastify.css"
import { FiSend, FiUser } from "react-icons/fi"

type Message = {
  role: "user" | "bot"
  content: string
}

export default function AskQuestion() {
  const [userId, setUserId] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [inputMessage, setInputMessage] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const chatContainerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight
    }
  }, [chatContainerRef]) // Corrected dependency

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!inputMessage.trim()) return

    const newMessage: Message = { role: "user", content: inputMessage }
    setMessages((prevMessages) => [...prevMessages, newMessage])
    setInputMessage("")
    setIsLoading(true)

    try {
      // Simulating API call
      await new Promise((resolve) => setTimeout(resolve, 1000))
      const botResponse: Message = {
        role: "bot",
        content: `Here's a response for user ${userId}: ${inputMessage}`,
      }
      setMessages((prevMessages) => [...prevMessages, botResponse])
    } catch (error) {
      toast.error("An error occurred. Please try again.")
    } finally {
      setIsLoading(false)
    }
  }

  const handleUserIdSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const form = e.target as HTMLFormElement
    const userIdInput = form.elements.namedItem("userId") as HTMLInputElement
    if (userIdInput.value.trim()) {
      setUserId(userIdInput.value.trim())
      setMessages([
        {
          role: "bot",
          content: `Hello! How can I assist you today?`,
        },
      ])
    }
  }

  return (
    <div className="max-w-4xl mx-auto">
      <motion.h1
        className="text-4xl font-bold mb-8 text-center text-indigo-800 dark:text-indigo-200"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        Ask a Question
      </motion.h1>

      {!userId ? (
        <motion.form
          onSubmit={handleUserIdSubmit}
          className="card p-8 bg-white dark:bg-gray-800 shadow-lg"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.5 }}
        >
          <div className="mb-6">
            <label className="block text-gray-700 dark:text-gray-300 text-sm font-bold mb-2" htmlFor="userId">
              <FiUser className="inline-block mr-2" />
              User ID
            </label>
            <input className="input" id="userId" name="userId" type="text" placeholder="Enter your User ID" required />
          </div>
          <div className="flex items-center justify-end">
            <motion.button
              className="btn bg-indigo-600 hover:bg-indigo-700 text-white flex items-center"
              type="submit"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              Start Chat
            </motion.button>
          </div>
        </motion.form>
      ) : (
        <motion.div
          className="card p-8 bg-white dark:bg-gray-800 shadow-lg"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.5 }}
        >
          <div ref={chatContainerRef} className="h-96 overflow-y-auto mb-4 p-4 bg-gray-100 dark:bg-gray-700 rounded-lg">
            <AnimatePresence>
              {messages.map((message, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ duration: 0.3 }}
                  className={`mb-4 ${message.role === "user" ? "text-right" : "text-left"}`}
                >
                  <span
                    className={`inline-block p-2 rounded-lg ${
                      message.role === "user"
                        ? "bg-indigo-600 text-white"
                        : "bg-gray-300 dark:bg-gray-600 text-gray-800 dark:text-gray-200"
                    }`}
                  >
                    {message.content}
                  </span>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
          <form onSubmit={handleSendMessage} className="flex items-center">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder="Type your message here..."
              className="input flex-grow mr-2"
              disabled={isLoading}
            />
            <motion.button
              className="btn bg-indigo-600 hover:bg-indigo-700 text-white flex items-center"
              type="submit"
              disabled={isLoading}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <FiSend className="mr-2" />
              {isLoading ? "Sending..." : "Send"}
            </motion.button>
          </form>
        </motion.div>
      )}
      <ToastContainer position="bottom-right" autoClose={3000} />
    </div>
  )
}

