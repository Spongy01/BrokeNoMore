# BrokeNoMore Frontend — Design Spec

**Date:** 2026-05-06  
**Stack:** Next.js 14 (App Router) · Shadcn/ui · Tailwind · TanStack Query · React Context  
**API contract:** `API_SPEC.md` (source of truth)  
**Base URL:** `http://localhost:8000`

---

## Visual Design

- **Color scheme:** Indigo/Violet
  - Nav background: `#312e81` (indigo-900)
  - Active nav item: `#3730a3` (indigo-800)
  - Accent / primary button: `#6366f1` (indigo-500)
  - Page background: `#eef2ff` (indigo-50)
  - Card border: `#c7d2fe` (indigo-200)
  - Card background: white
  - Nav text / muted: `#a5b4fc` (indigo-300)
  - Debit amounts: `#dc2626` (red-600)
  - Credit amounts: `#16a34a` (green-600)
- **Typography:** Inter (Google Fonts via `next/font`)
- **Mode:** Light only

---

## Architecture

### Directory structure

```
frontend/                          # Built from scratch — existing files deleted
├── app/
│   ├── (auth)/                    # Unauthenticated route group
│   │   ├── layout.tsx             # Centered card layout, no nav
│   │   ├── login/page.tsx
│   │   ├── register/page.tsx
│   │   ├── forgot-password/page.tsx
│   │   └── reset-password/page.tsx
│   ├── (protected)/               # Authenticated route group
│   │   ├── layout.tsx             # Top nav layout
│   │   ├── dashboard/page.tsx
│   │   └── chat/page.tsx
│   ├── layout.tsx                 # Root: QueryClientProvider + AuthProvider
│   └── globals.css
├── lib/
│   ├── api.ts                     # Fetch wrapper
│   └── auth-context.tsx           # AuthContext + useAuth
├── components/
│   ├── ui/                        # Shadcn components
│   ├── nav.tsx                    # Top nav bar
│   └── upload-csv-dialog.tsx      # CSV upload modal
├── middleware.ts                  # Route protection
└── package.json
```

### Key dependencies (additions to scaffold)

| Package | Purpose |
|---|---|
| `@tanstack/react-query` | Server state, data fetching |
| `@tanstack/react-query-devtools` | Dev tooling |
| `react-hook-form` | Form state (already present) |
| `zod` | Schema validation (already present) |
| `@hookform/resolvers` | RHF + Zod bridge (already present) |

---

## Auth Layer

### `lib/auth-context.tsx`

- Exports `AuthProvider` and `useAuth` hook
- State: `{ token: string | null, user: { email: string } | null }`
- `login(token, email)`: writes token to `localStorage` key `brokenomore_token`, writes same value to a client-accessible cookie `brokenomore_token` (for middleware), updates state
- `logout()`: clears localStorage, clears cookie, calls `POST /auth/logout`, redirects to `/login`
- Initialises from localStorage on mount (handles page refresh)

### `lib/api.ts`

- Thin `apiFetch(path, options)` wrapper around `fetch`
- Reads token from `localStorage` on each call
- Attaches `Authorization: Bearer <token>` header automatically
- On **401**: calls `logout()` from auth context and redirects to `/login`
- Exports typed helpers: `apiGet`, `apiPost`, `apiPostForm` (multipart)

### `middleware.ts`

- Protects `/dashboard` and `/chat`
- Reads `brokenomore_token` cookie (set by `auth-context.tsx` on login)
- If missing: redirects to `/login`
- Does **not** validate the JWT — real validation happens on the API (returns 401 if expired, which `api.ts` handles)
- Redirects `/` → `/dashboard` for authenticated users, `/login` for unauthenticated

---

## Pages

### `/login` — `app/(auth)/login/page.tsx`

- Tabbed card shared with `/register` (Login | Create Account tabs)
- Fields: `email`, `password`
- "Forgot password?" link → `/forgot-password`
- On submit: `POST /auth/login` → store token via `login()` → redirect `/dashboard`
- Errors: inline below form (`"Invalid credentials"`, `"Account inactive"`)
- If already authenticated: redirect to `/dashboard`

### `/register` — `app/(auth)/register/page.tsx`

- Same tabbed card as login (tab switches between pages via `Link`)
- Fields: `email`, `password`
- On submit: `POST /auth/register` → redirect `/login` with success toast
- Errors: inline (`"Email already registered"`, validation errors)

### `/forgot-password` — `app/(auth)/forgot-password/page.tsx`

- Simple card: email field + submit button
- On submit: `POST /auth/forgot-password` → always shows success banner regardless of outcome (API always returns 204)
- Success message: "Check your email for a reset link"
- Back to login link

### `/reset-password` — `app/(auth)/reset-password/page.tsx`

- Reads `?token=` from `useSearchParams()`
- If no token in URL: show error state ("Invalid or missing reset link")
- Fields: `new_password`
- On submit: `POST /auth/reset-password` with `{ token, new_password }` → redirect `/login` with success toast
- Errors: inline (`"Invalid or expired reset token"`)

### `/dashboard` — `app/(protected)/dashboard/page.tsx`

- Data: `GET /transactions` via `useQuery` → array of transaction objects
- **Summary cards row** (computed client-side from transactions):
  - Total Spend (sum of debits)
  - Total Income (sum of credits)
  - Upload CSV card/button → opens `UploadCsvDialog`
- **Transaction table** (Shadcn `Table`):
  - Columns: Description, Date, Category, Amount
  - Amount: red for debits, green for credits
  - Category: indigo badge
  - Sorted by date descending
  - Empty state: "No transactions yet — upload a CSV to get started"
- **`UploadCsvDialog`** (Shadcn `Dialog`):
  - Fields: file input (`.csv`), source selector (`Chase Checking` | `Discover Credit`)
  - On submit: `POST /transactions/upload-csv` (multipart)
  - Success: shows `imported` / `skipped` counts, closes dialog, invalidates `GET /transactions` query
  - Error: inline message

### `/chat` — `app/(protected)/chat/page.tsx`

- Full-page chat interface
- `thread_id` stored in component state (not persisted across page loads — new thread on each visit)
- First message: `POST /query` with `{ message }` (no `thread_id`) → server returns `thread_id` → stored in state
- Follow-up messages: `POST /query` with `{ message, thread_id }`
- Message list: user messages right-aligned (indigo bubble), AI messages left-aligned (white card with border)
- Typing indicator (three dots) while awaiting response
- Input: rounded pill input + indigo send button
- Welcome message rendered before any user interaction: "Hi! I'm your finance AI. Ask me anything about your spending."
- Error state: inline error below input if API call fails

---

## Auth Layout — `app/(auth)/layout.tsx`

- Full-screen centered layout (`min-h-screen flex items-center justify-center`)
- Background: `#eef2ff` (indigo-50)
- Branding at top: `🪙 BrokeNoMore` in indigo-900, subtitle in indigo-400
- Card: white, `border border-indigo-200`, `rounded-xl shadow-sm`, max-width `sm` (384px)

---

## Protected Layout — `app/(protected)/layout.tsx`

- Top nav: `#312e81` background, full width
- Left: `🪙 BrokeNoMore` logo in indigo-300
- Center-left: nav links — Dashboard, Chat
- Active link: `#3730a3` background pill
- Right: user email with dropdown → Logout
- Page content below nav: `#eef2ff` background, padded container

---

## Token Lifetime & Expiry

- JWT expires after 1 hour (`JWT_LIFETIME_SECONDS=3600`)
- On any `401` from `api.ts`: `logout()` → clears state + cookie + localStorage → redirect `/login`
- No silent refresh (out of scope)

---

## Out of Scope

- Dark mode
- Pagination on transaction table
- Manual transaction creation (POST /transactions)
- Token refresh
