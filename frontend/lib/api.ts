const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

function getToken(): string | null {
  if (typeof window === 'undefined') return null
  return localStorage.getItem('brokenomore_token')
}

function clearAuthAndRedirect(): never {
  localStorage.removeItem('brokenomore_token')
  localStorage.removeItem('brokenomore_email')
  document.cookie = 'brokenomore_token=; path=/; max-age=0'
  window.location.href = '/login'
  throw new Error('Unauthorized')
}

async function parseError(res: Response): Promise<string> {
  try {
    const body = await res.json()
    if (Array.isArray(body.detail)) {
      return body.detail[0]?.msg ?? 'Validation error'
    }
    return body.detail ?? 'Request failed'
  } catch {
    return 'Request failed'
  }
}

async function request(path: string, options: RequestInit): Promise<Response> {
  const token = getToken()
  const headers = new Headers(options.headers)
  if (token) headers.set('Authorization', `Bearer ${token}`)
  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers })
  if (res.status === 401) clearAuthAndRedirect()
  return res
}

export async function apiGet<T>(path: string): Promise<T> {
  const res = await request(path, {})
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}

export async function apiPost<T>(path: string, body: object): Promise<T> {
  const res = await request(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (res.status === 204) return undefined as T
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}

export async function apiPostForm<T>(path: string, form: FormData): Promise<T> {
  const res = await request(path, { method: 'POST', body: form })
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}
