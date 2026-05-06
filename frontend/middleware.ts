import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

const PROTECTED = ['/dashboard', '/chat']
const AUTH_PAGES = ['/login', '/register', '/forgot-password', '/reset-password']

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl
  const token = request.cookies.get('brokenomore_token')?.value

  if (pathname === '/') {
    const dest = token ? '/dashboard' : '/login'
    return NextResponse.redirect(new URL(dest, request.url))
  }

  const isProtected = PROTECTED.some(p => pathname.startsWith(p))
  if (isProtected && !token) {
    return NextResponse.redirect(new URL('/login', request.url))
  }

  const isAuthPage = AUTH_PAGES.some(p => pathname.startsWith(p))
  if (isAuthPage && token) {
    return NextResponse.redirect(new URL('/dashboard', request.url))
  }

  return NextResponse.next()
}

export const config = {
  matcher: [
    '/',
    '/dashboard/:path*',
    '/chat/:path*',
    '/login',
    '/register',
    '/forgot-password',
    '/reset-password',
  ],
}
