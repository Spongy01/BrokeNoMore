import { ReactNode } from 'react'

export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-indigo-50 px-4">
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-extrabold text-indigo-900">🪙 BrokeNoMore</h1>
        <p className="text-sm text-indigo-400 mt-1">Your personal finance AI</p>
      </div>
      <div className="w-full max-w-sm bg-white rounded-xl border border-indigo-200 shadow-sm p-8">
        {children}
      </div>
    </div>
  )
}
