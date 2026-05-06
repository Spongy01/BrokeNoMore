'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiGet } from '@/lib/api'
import type { Transaction } from '@/lib/types'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import { Upload } from 'lucide-react'
import UploadCsvDialog from '@/components/upload-csv-dialog'

function formatCurrency(amount: string | number) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(
    Number(amount)
  )
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

export default function DashboardPage() {
  const [uploadOpen, setUploadOpen] = useState(false)

  const { data: transactions = [], isLoading, isError } = useQuery<Transaction[]>({
    queryKey: ['transactions'],
    queryFn: () => apiGet<Transaction[]>('/transactions'),
  })

  const sorted = [...transactions].sort(
    (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()
  )

  const totalSpend = transactions
    .filter(t => t.transaction_type === 'debit')
    .reduce((sum, t) => sum + Number(t.amount), 0)

  const totalIncome = transactions
    .filter(t => t.transaction_type === 'credit')
    .reduce((sum, t) => sum + Number(t.amount), 0)

  return (
    <>
      <div className="grid grid-cols-3 gap-4 mb-6">
        <Card className="border-indigo-200">
          <CardHeader className="pb-1">
            <CardTitle className="text-xs font-semibold uppercase tracking-wide text-indigo-500">
              Total Spend
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-extrabold text-indigo-900">
              {formatCurrency(totalSpend)}
            </p>
            <p className="text-xs text-gray-400 mt-0.5">All time</p>
          </CardContent>
        </Card>

        <Card className="border-indigo-200">
          <CardHeader className="pb-1">
            <CardTitle className="text-xs font-semibold uppercase tracking-wide text-green-600">
              Total Income
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-extrabold text-green-700">
              {formatCurrency(totalIncome)}
            </p>
            <p className="text-xs text-gray-400 mt-0.5">All time</p>
          </CardContent>
        </Card>

        <Card
          className="border-indigo-200 bg-indigo-500 cursor-pointer hover:bg-indigo-600 transition-colors"
          onClick={() => setUploadOpen(true)}
        >
          <CardContent className="flex flex-col items-center justify-center h-full py-6 gap-1">
            <Upload className="w-6 h-6 text-white" />
            <p className="text-sm font-bold text-white">Upload CSV</p>
            <p className="text-xs text-indigo-200">Chase · Discover</p>
          </CardContent>
        </Card>
      </div>

      <Card className="border-indigo-200">
        <CardHeader className="flex flex-row items-center justify-between pb-3 border-b border-indigo-100">
          <CardTitle className="text-base text-indigo-900">Transactions</CardTitle>
          <span className="text-xs text-indigo-400">{transactions.length} records</span>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading && (
            <p className="text-sm text-indigo-400 text-center py-10">Loading transactions…</p>
          )}
          {isError && (
            <p className="text-sm text-red-500 text-center py-10">
              Failed to load transactions.
            </p>
          )}
          {!isLoading && !isError && transactions.length === 0 && (
            <div className="text-center py-12">
              <p className="text-gray-500 text-sm mb-3">No transactions yet.</p>
              <Button
                onClick={() => setUploadOpen(true)}
                className="bg-indigo-500 hover:bg-indigo-600 text-white text-sm"
              >
                <Upload className="w-4 h-4 mr-1.5" /> Upload a CSV to get started
              </Button>
            </div>
          )}
          {!isLoading && sorted.length > 0 && (
            <Table>
              <TableHeader>
                <TableRow className="bg-indigo-50 hover:bg-indigo-50">
                  <TableHead className="text-indigo-500 text-xs uppercase tracking-wide">
                    Description
                  </TableHead>
                  <TableHead className="text-indigo-500 text-xs uppercase tracking-wide">
                    Date
                  </TableHead>
                  <TableHead className="text-indigo-500 text-xs uppercase tracking-wide">
                    Category
                  </TableHead>
                  <TableHead className="text-indigo-500 text-xs uppercase tracking-wide text-right">
                    Amount
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {sorted.map(t => (
                  <TableRow key={t.id} className="hover:bg-indigo-50/50">
                    <TableCell className="font-medium text-gray-800 text-sm">
                      {t.description}
                    </TableCell>
                    <TableCell className="text-gray-500 text-sm">{formatDate(t.date)}</TableCell>
                    <TableCell>
                      <Badge
                        variant="secondary"
                        className={
                          t.transaction_type === 'credit'
                            ? 'bg-green-50 text-green-700 border-green-200'
                            : 'bg-indigo-50 text-indigo-700 border-indigo-200'
                        }
                      >
                        {t.category}
                      </Badge>
                    </TableCell>
                    <TableCell
                      className={`text-right text-sm font-semibold ${
                        t.transaction_type === 'credit' ? 'text-green-600' : 'text-red-500'
                      }`}
                    >
                      {t.transaction_type === 'credit' ? '+' : '-'}
                      {formatCurrency(t.amount)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <UploadCsvDialog open={uploadOpen} onOpenChange={setUploadOpen} />
    </>
  )
}
