"use client"

import { useState } from "react"
import { useForm, type SubmitHandler } from "react-hook-form"
import { motion, AnimatePresence } from "framer-motion"
import { toast, ToastContainer } from "react-toastify"
import "react-toastify/dist/ReactToastify.css"
import { FiSend, FiUser, FiHelpCircle } from "react-icons/fi"

type FormInputs = {
  query_user_id: string
  question: string
}

export default function AskQuestion() {
  const [response, setResponse] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<FormInputs>()

  const onSubmit: SubmitHandler<FormInputs> = async (data) => {
    setIsLoading(true)
    try {
      // Simulating API call
      await new Promise((resolve) => setTimeout(resolve, 1000))
      const mockResponse = `Here's a response for user ${data.query_user_id}: ${data.question}`
      setResponse(mockResponse)
      toast.success("Question submitted successfully!")
      reset()
    } catch (error) {
      toast.error("An error occurred. Please try again.")
    } finally {
      setIsLoading(false)
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
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <motion.form
          onSubmit={handleSubmit(onSubmit)}
          className="card p-8 bg-white dark:bg-gray-800 shadow-lg"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2, duration: 0.5 }}
        >
          <div className="mb-6">
            <label className="block text-gray-700 dark:text-gray-300 text-sm font-bold mb-2" htmlFor="query_user_id">
              <FiUser className="inline-block mr-2" />
              User ID
            </label>
            <input
              className={`input ${errors.query_user_id ? "border-red-500" : ""}`}
              id="query_user_id"
              {...register("query_user_id", { required: "User ID is required" })}
              placeholder="Enter your User ID"
            />
            {errors.query_user_id && <p className="text-red-500 text-xs italic mt-1">{errors.query_user_id.message}</p>}
          </div>
          <div className="mb-6">
            <label className="block text-gray-700 dark:text-gray-300 text-sm font-bold mb-2" htmlFor="question">
              <FiHelpCircle className="inline-block mr-2" />
              Question
            </label>
            <textarea
              className={`input h-32 ${errors.question ? "border-red-500" : ""}`}
              id="question"
              {...register("question", { required: "Question is required" })}
              placeholder="Type your question here..."
            ></textarea>
            {errors.question && <p className="text-red-500 text-xs italic mt-1">{errors.question.message}</p>}
          </div>
          <div className="flex items-center justify-end">
            <motion.button
              className="btn bg-indigo-600 hover:bg-indigo-700 text-white flex items-center"
              type="submit"
              disabled={isLoading}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              {isLoading ? (
                "Submitting..."
              ) : (
                <>
                  <FiSend className="mr-2" />
                  Ask Question
                </>
              )}
            </motion.button>
          </div>
        </motion.form>
        <motion.div
          className="card p-8 bg-gradient-to-br from-indigo-500 to-purple-600 text-white"
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.4, duration: 0.5 }}
        >
          <h2 className="text-2xl font-bold mb-4">How It Works</h2>
          <ol className="list-decimal list-inside space-y-4">
            <li>Enter your User ID in the form.</li>
            <li>Type your financial question in the text area.</li>
            <li>Click the "Ask Question" button to submit.</li>
            <li>Receive a personalized response based on your query.</li>
          </ol>
          <div className="mt-8">
            <h3 className="text-xl font-semibold mb-2">Tips for Great Questions</h3>
            <ul className="list-disc list-inside space-y-2">
              <li>Be specific about your financial situation</li>
              <li>Provide relevant details (e.g., account types, goals)</li>
              <li>Ask one question at a time for clearer answers</li>
            </ul>
          </div>
        </motion.div>
      </div>
      <AnimatePresence>
        {response && (
          <motion.div
            className="mt-8 p-6 bg-white dark:bg-gray-800 rounded-lg shadow-lg"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.3 }}
          >
            <h2 className="text-2xl font-semibold mb-4 text-indigo-700 dark:text-indigo-300">Your Answer</h2>
            <p className="text-gray-700 dark:text-gray-300 text-lg leading-relaxed">{response}</p>
          </motion.div>
        )}
      </AnimatePresence>
      <ToastContainer position="bottom-right" autoClose={3000} />
    </div>
  )
}

