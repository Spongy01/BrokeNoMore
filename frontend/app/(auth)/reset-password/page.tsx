import { Suspense } from 'react'
import ResetForm from './reset-form'

export default function ResetPasswordPage() {
  return (
    <>
      <h2 className="text-xl font-bold text-indigo-900 mb-1">Set new password</h2>
      <p className="text-sm text-gray-500 mb-6">Choose a strong password for your account.</p>
      <Suspense fallback={<p className="text-sm text-indigo-400">Loading…</p>}>
        <ResetForm />
      </Suspense>
    </>
  )
}
