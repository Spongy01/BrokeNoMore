'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { toast } from 'sonner'
import { apiPost } from '@/lib/api'
import type { RegisterResponse } from '@/lib/types'
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
  email: z.string().email('Enter a valid email'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
})
type FormValues = z.infer<typeof schema>

export default function RegisterPage() {
  const router = useRouter()
  const [error, setError] = useState<string | null>(null)

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { email: '', password: '' },
  })

  async function onSubmit(values: FormValues) {
    setError(null)
    try {
      await apiPost<RegisterResponse>('/auth/register', values)
      toast.success('Account created! Please sign in.')
      router.push('/login')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed')
    }
  }

  return (
    <>
      <div className="flex bg-indigo-50 rounded-lg p-1 mb-6">
        <Link
          href="/login"
          className="flex-1 text-center py-1.5 text-sm text-indigo-500 hover:text-indigo-700"
        >
          Sign In
        </Link>
        <span className="flex-1 text-center bg-white rounded-md py-1.5 text-sm font-semibold text-indigo-900 shadow-sm">
          Create Account
        </span>
      </div>

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
          <FormField
            control={form.control}
            name="email"
            render={({ field }) => (
              <FormItem>
                <FormLabel className="text-indigo-900">Email</FormLabel>
                <FormControl>
                  <Input
                    placeholder="you@example.com"
                    type="email"
                    className="border-indigo-200 bg-indigo-50 focus-visible:ring-indigo-400"
                    {...field}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="password"
            render={({ field }) => (
              <FormItem>
                <FormLabel className="text-indigo-900">Password</FormLabel>
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
            {form.formState.isSubmitting ? 'Creating account…' : 'Create Account'}
          </Button>
        </form>
      </Form>
    </>
  )
}
