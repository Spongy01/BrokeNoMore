"use client"
import Link from "next/link"
import { motion } from "framer-motion"

export default function Home() {
  return (
    <div className="max-w-4xl mx-auto">
      <motion.h1
        className="text-4xl font-bold mb-8 text-center text-indigo-800 dark:text-indigo-200"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        Welcome to Financial App
      </motion.h1>
      <motion.p
        className="text-xl mb-12 text-center text-gray-600 dark:text-gray-300"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2, duration: 0.5 }}
      >
        Manage your finances with ease using our powerful tools.
      </motion.p>
      <motion.div
        className="grid grid-cols-1 md:grid-cols-3 gap-6"
        variants={{
          hidden: { opacity: 0 },
          show: {
            opacity: 1,
            transition: {
              staggerChildren: 0.2,
            },
          },
        }}
        initial="hidden"
        animate="show"
      >
        <FeatureCard
          title="Update Transactions"
          description="Keep your financial records up to date."
          link="/update-transaction"
          icon="💰"
        />
        <FeatureCard
          title="Ask Questions"
          description="Get insights about your financial data."
          link="/ask-question"
          icon="❓"
        />
        <FeatureCard
          title="Visualize Data"
          description="See your finances come to life with charts."
          link="/visualize-data"
          icon="📊"
        />
      </motion.div>
    </div>
  )
}

function FeatureCard({
  title,
  description,
  link,
  icon,
}: {
  title: string
  description: string
  link: string
  icon: string
}) {
  return (
    <motion.div
      className="card p-6 flex flex-col items-center text-center"
      variants={{
        hidden: { opacity: 0, y: 20 },
        show: { opacity: 1, y: 0 },
      }}
    >
      <div className="text-4xl mb-4">{icon}</div>
      <h2 className="text-2xl font-semibold mb-4 text-indigo-700 dark:text-indigo-300">{title}</h2>
      <p className="text-gray-600 dark:text-gray-400 mb-4">{description}</p>
      <Link href={link} className="btn mt-auto">
        Learn more
      </Link>
    </motion.div>
  )
}