"use client";

import { useState } from "react";
import { Bar, Doughnut, Radar } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  PointElement,
  LineElement,
  RadialLinearScale
} from "chart.js";

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  PointElement,
  LineElement,
  RadialLinearScale,
  Title,
  Tooltip,
  Legend
);

export default function VisualizeData() {
  const [chartData, setChartData] = useState<any>(null);
  const [doughnutData, setDoughnutData] = useState<any>(null);
  const [radarData, setRadarData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [noData, setNoData] = useState(false);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setNoData(false);

    const formData = new FormData(event.currentTarget);
    const userId = formData.get("visualize_user_id");

    try {
      const response = await fetch(`http://127.0.0.1:5000/get_transactions?user_id=${userId}`);

      if (!response.ok) {
        throw new Error("Failed to fetch transactions");
      }

      const data = await response.json();
      if (!data.transactions || data.transactions.length === 0) {
        setNoData(true);
        setLoading(false);
        return;
      }

      const transactions = data.transactions;
      const categories = [...new Set(transactions.map((item: any) => item.category))];
      const categoryAmounts = categories.map((category) =>
        transactions.filter((item: any) => item.category === category).reduce((sum, item) => sum + parseFloat(item.amount), 0)
      );

      setChartData({
        labels: categories,
        datasets: [{
          label: "Amount",
          data: categoryAmounts,
          backgroundColor: [
            "rgba(255, 99, 132, 0.6)",
            "rgba(54, 162, 235, 0.6)",
            "rgba(255, 206, 86, 0.6)",
            "rgba(75, 192, 192, 0.6)",
            "rgba(153, 102, 255, 0.6)",
            "rgba(255, 159, 64, 0.6)"
          ],
          borderColor: [
            "rgba(255, 99, 132, 1)",
            "rgba(54, 162, 235, 1)",
            "rgba(255, 206, 86, 1)",
            "rgba(75, 192, 192, 1)",
            "rgba(153, 102, 255, 1)",
            "rgba(255, 159, 64, 1)"
          ],
          borderWidth: 1,
        }],
      });

      setDoughnutData({
        labels: categories,
        datasets: [{
          data: categoryAmounts,
          backgroundColor: ["#FF5733", "#33FF57", "#3357FF", "#FFC300", "#C70039"],
        }],
      });

      setRadarData({
        labels: categories,
        datasets: [{
          label: "Spending Pattern",
          data: categoryAmounts,
          backgroundColor: "rgba(255, 99, 132, 0.2)",
          borderColor: "rgba(255, 99, 132, 1)",
          pointBackgroundColor: "rgba(255, 99, 132, 1)",
        }],
      });

      setLoading(false);
    } catch (error: any) {
      setError(error.message);
      setLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-4">
      <h1 className="text-3xl font-bold mb-8 text-center text-indigo-800">Visualize Data</h1>
      <form onSubmit={handleSubmit} className="bg-white shadow-md rounded px-8 pt-6 pb-8 mb-4">
        <div className="mb-4">
          <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="visualize_user_id">User ID</label>
          <input className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight" id="visualize_user_id" name="visualize_user_id" type="text" placeholder="User ID" required />
        </div>
        <div className="flex items-center justify-center">
          <button className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2 px-4 rounded" type="submit">
            {loading ? "Loading..." : "Visualize"}
          </button>
        </div>
      </form>

      {error && <p className="text-red-500 text-center">{error}</p>}
      {noData && <p className="text-gray-600 text-center">No transactions found for this user.</p>}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {chartData && (
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h2 className="text-center text-lg font-bold mb-2">Bar Chart: Category-wise Spending</h2>
            <Bar data={chartData} options={{ responsive: true, maintainAspectRatio: true }} />
          </div>
        )}
        {doughnutData && (
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h2 className="text-center text-lg font-bold mb-2">Doughnut Chart: Category Distribution</h2>
            <Doughnut data={doughnutData} options={{ responsive: true, maintainAspectRatio: true }} />
          </div>
        )}
        {radarData && (
          <div className="bg-white p-10 rounded-lg shadow-md md:col-span-2">
            <h2 className="text-center text-lg font-bold mb-2">Radar Chart: Spending Pattern</h2>
            <Radar data={radarData} options={{ responsive: true, maintainAspectRatio: true }} />
          </div>
        )}
      </div>
    </div>
  );
}
