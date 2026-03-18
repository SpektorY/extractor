const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"

const getToken = (): string | null => localStorage.getItem("access_token")
const getVolunteerToken = (): string | null => localStorage.getItem("volunteer_token")

export interface LoginResponse {
  access_token: string
  token_type: string
}

export async function login(password: string): Promise<LoginResponse> {
  const res = await fetch(`${API_BASE}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ password }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    const msg = typeof err.detail === "string" ? err.detail : "התחברות נכשלה"
    throw new Error(msg)
  }
  return res.json() as Promise<LoginResponse>
}

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken()
  const headers: HeadersInit = { ...options.headers }
  if (token) {
    (headers as Record<string, string>)["Authorization"] = `Bearer ${token}`
  }
  if (options.body && !(options.body instanceof FormData)) {
    (headers as Record<string, string>)["Content-Type"] = "application/json"
  }
  const res = await fetch(`${API_BASE}${path}`, { ...options, headers })
  if (res.status === 401) {
    localStorage.removeItem("access_token")
    window.location.href = "/login"
    throw new Error("Unauthorized")
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(typeof err.detail === "string" ? err.detail : JSON.stringify(err.detail))
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

export async function volunteerApiRequest<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getVolunteerToken()
  const headers: HeadersInit = { ...options.headers }
  if (token) {
    (headers as Record<string, string>)["Authorization"] = `Bearer ${token}`
  }
  if (options.body && !(options.body instanceof FormData)) {
    (headers as Record<string, string>)["Content-Type"] = "application/json"
  }
  const res = await fetch(`${API_BASE}${path}`, { ...options, headers })
  if (res.status === 401) {
    localStorage.removeItem("volunteer_token")
    throw new Error("Unauthorized")
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(typeof err.detail === "string" ? err.detail : JSON.stringify(err.detail))
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

export function setAccessToken(token: string): void {
  localStorage.setItem("access_token", token)
}

export function clearAccessToken(): void {
  localStorage.removeItem("access_token")
}

export interface VolunteerOtpVerifyResponse {
  access_token: string
  token_type: string
  volunteer: {
    id: number
    first_name: string
    last_name: string
    phone: string
    group_tag: string | null
    living_area: string | null
    anonymized: boolean
    status: "pending" | "approved"
  }
}

export async function requestVolunteerOtp(phone: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/v1/public/auth/request-otp`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ phone }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(typeof err.detail === "string" ? err.detail : "שליחת קוד נכשלה")
  }
}

export async function verifyVolunteerOtp(phone: string, code: string): Promise<VolunteerOtpVerifyResponse> {
  const res = await fetch(`${API_BASE}/api/v1/public/auth/verify-otp`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ phone, code }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(typeof err.detail === "string" ? err.detail : "אימות קוד נכשל")
  }
  return res.json() as Promise<VolunteerOtpVerifyResponse>
}

export function setVolunteerAccessToken(token: string): void {
  localStorage.setItem("volunteer_token", token)
}

export function clearVolunteerAccessToken(): void {
  localStorage.removeItem("volunteer_token")
}

export function hasVolunteerToken(): boolean {
  return Boolean(getVolunteerToken())
}
