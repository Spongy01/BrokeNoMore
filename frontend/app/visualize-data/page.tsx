"use client"

import { useState } from "react"
import { Bar } from "react-chartjs-2"
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from "chart.js"

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend)

export default function VisualizeData() {
  const [chartData, setChartData] = useState<any>(null)

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const formData = new FormData(event.currentTarget)
    const userId = formData.get("visualize_user_id")

    // Dummy data - replace with actual API call
    const data = [
      { amount: 50, category: "Food" },
      { amount: 100, category: "Transport" },
      { amount: 200, category: "Entertainment" },
    ]

    setChartData({
      labels: data.map((item) => item.category),
      datasets: [
        {
          label: "Amount",
          data: data.map((item) => item.amount),
          backgroundColor: "rgba(75, 192, 192, 0.6)",
        },
      ],
    })
  }

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-8 text-center text-indigo-800">Visualize Data</h1>
      <form onSubmit={handleSubmit} className="bg-white shadow-md rounded px-8 pt-6 pb-8 mb-4">
        <div className="mb-4">
          <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="visualize_user_id">
            User ID
          </label>
          <input
            className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
            id="visualize_user_id"
            name="visualize_user_id"
            type="text"
            placeholder="User ID"
            required
          />
        </div>
        <div className="flex items-center justify-between">
          <button
            className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline transition-colors"
            type="submit"
          >
            Visualize
          </button>
        </div>
      </form>
      {chartData && (
        <div className="bg-white p-6 rounded-lg shadow-md">
          <Bar
            data={chartData}
            options={{
              responsive: true,
              plugins: { legend: { position: "top" as const }, title: { display: true, text: "Transaction Data" } },
            }}
          />
        </div>
      )}
    </div>
  )
}

