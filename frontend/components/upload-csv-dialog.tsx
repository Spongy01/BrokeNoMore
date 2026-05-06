'use client'

import { useState, useRef } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { apiPostForm } from '@/lib/api'
import type { UploadResponse } from '@/lib/types'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'

interface Props {
  open: boolean
  onOpenChange: (open: boolean) => void
}

const SOURCES = ['Chase Checking', 'Discover Credit'] as const
type Source = typeof SOURCES[number]

export default function UploadCsvDialog({ open, onOpenChange }: Props) {
  const queryClient = useQueryClient()
  const fileRef = useRef<HTMLInputElement>(null)
  const [source, setSource] = useState<Source | ''>('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<UploadResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  function handleClose() {
    setResult(null)
    setError(null)
    setSource('')
    if (fileRef.current) fileRef.current.value = ''
    onOpenChange(false)
  }

  async function handleUpload() {
    const file = fileRef.current?.files?.[0]
    if (!file) { setError('Please select a CSV file.'); return }
    if (!source) { setError('Please select a source.'); return }

    setError(null)
    setLoading(true)

    const form = new FormData()
    form.append('file', file)
    form.append('source', source)

    try {
      const data = await apiPostForm<UploadResponse>('/transactions/upload-csv', form)
      setResult(data)
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
      toast.success(`Imported ${data.imported} transactions`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="text-indigo-900">Upload CSV</DialogTitle>
        </DialogHeader>

        {result ? (
          <div className="space-y-3">
            <div className="bg-green-50 border border-green-200 rounded-md p-4 text-sm text-green-800">
              <p className="font-semibold">Import complete</p>
              <p>{result.imported} transactions imported · {result.skipped} skipped</p>
            </div>
            {result.skipped_transactions.length > 0 && (
              <div className="text-xs text-gray-500 max-h-32 overflow-y-auto space-y-0.5">
                <p className="font-medium text-gray-700 mb-1">Skipped rows:</p>
                {result.skipped_transactions.map((s, i) => (
                  <p key={i} className="truncate">• {s}</p>
                ))}
              </div>
            )}
            <DialogFooter>
              <Button onClick={handleClose} className="bg-indigo-500 hover:bg-indigo-600 text-white">
                Done
              </Button>
            </DialogFooter>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="space-y-1.5">
              <Label className="text-indigo-900">CSV File</Label>
              <input
                ref={fileRef}
                type="file"
                accept=".csv"
                className="block w-full text-sm text-gray-500 file:mr-3 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:bg-indigo-50 file:text-indigo-700 file:text-sm file:font-medium hover:file:bg-indigo-100 cursor-pointer"
              />
            </div>

            <div className="space-y-1.5">
              <Label className="text-indigo-900">Source</Label>
              <Select value={source} onValueChange={(v) => setSource(v as Source)}>
                <SelectTrigger className="border-indigo-200">
                  <SelectValue placeholder="Select bank source" />
                </SelectTrigger>
                <SelectContent>
                  {SOURCES.map(s => (
                    <SelectItem key={s} value={s}>{s}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {error && (
              <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-md px-3 py-2">
                {error}
              </p>
            )}

            <DialogFooter>
              <Button variant="outline" onClick={handleClose} disabled={loading}>
                Cancel
              </Button>
              <Button
                onClick={handleUpload}
                disabled={loading}
                className="bg-indigo-500 hover:bg-indigo-600 text-white"
              >
                {loading ? 'Uploading…' : 'Upload'}
              </Button>
            </DialogFooter>
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}
