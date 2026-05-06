export interface Transaction {
  id: number
  user_id: string
  amount: string
  transaction_type: 'credit' | 'debit'
  category: string
  description: string
  date: string
  source: string | null
  created_at: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
}

export interface RegisterResponse {
  id: string
  email: string
  created_at: string
}

export interface UploadResponse {
  imported: number
  skipped: number
  skipped_transactions: string[]
}

export interface QueryResponse {
  response: string
  thread_id: string
}
