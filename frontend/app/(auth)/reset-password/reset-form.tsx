'use client'

import { useState } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { toast } from 'sonner'
import { apiPost } from '@/lib/api'
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'

const schema = z.object({
  new_password: z.string().min(8, 'Password must be at least 8 characters'),
})
type FormValues = z.infer<typeof schema>

export default function ResetForm() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const token = searchParams.get('token')
  const [error, setError] = useState<string | null>(null)

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { new_password: '' },
  })

  if (!token) {
    return (
      <div className="text-center">
        <p className="text-red-600 bg-red-50 border border-red-200 rounded-md px-4 py-3 text-sm mb-4">
          Invalid or missing reset link. Please request a new one.
        </p>
      </div>
    )
  }

  async function onSubmit(values: FormValues) {
    setError(null)
    try {
      await apiPost('/auth/reset-password', { token, new_password: values.new_password })
      toast.success('Password updated! Please sign in.')
      router.push('/login')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Reset failed')
    }
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
        <FormField
          control={form.control}
          name="new_password"
          render={({ field }) => (
            <FormItem>
              <FormLabel className="text-indigo-900">New Password</FormLabel>
              <FormControl>
                <Input
                  placeholder="Min. 8 characters"
                  type="password"
                  className="border-indigo-200 bg-indigo-50 focus-visible:ring-indigo-400"
                  {...field}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        {error && (
          <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-md px-3 py-2">
            {error}
          </p>
        )}

        <Button
          type="submit"
          className="w-full bg-indigo-500 hover:bg-indigo-600 text-white"
          disabled={form.formState.isSubmitting}
        >
          {form.formState.isSubmitting ? 'Updating…' : 'Set New Password'}
        </Button>
      </form>
    </Form>
  )
}
