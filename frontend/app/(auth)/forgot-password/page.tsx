'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
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

const schema = z.object({ email: z.string().email('Enter a valid email') })
type FormValues = z.infer<typeof schema>

export default function ForgotPasswordPage() {
  const [sent, setSent] = useState(false)

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { email: '' },
  })

  async function onSubmit(values: FormValues) {
    try {
      await apiPost('/auth/forgot-password', values)
    } catch {
      // API always returns 204 — ignore errors to prevent user enumeration
    }
    setSent(true)
  }

  return (
    <>
      <h2 className="text-xl font-bold text-indigo-900 mb-1">Reset your password</h2>
      <p className="text-sm text-gray-500 mb-6">
        Enter your email and we&apos;ll send a reset link.
      </p>

      {sent ? (
        <div className="bg-green-50 border border-green-200 rounded-md px-4 py-3 text-sm text-green-700 mb-4">
          ✓ Check your email for the reset link. It expires in 1 hour.
        </div>
      ) : (
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

            <Button
              type="submit"
              className="w-full bg-indigo-500 hover:bg-indigo-600 text-white"
              disabled={form.formState.isSubmitting}
            >
              {form.formState.isSubmitting ? 'Sending…' : 'Send Reset Link'}
            </Button>
          </form>
        </Form>
      )}

      <p className="mt-4 text-center text-sm text-indigo-500">
        <Link href="/login" className="hover:text-indigo-700">← Back to sign in</Link>
      </p>
    </>
  )
}
