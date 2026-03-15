import { useParams, Navigate } from "react-router-dom"

/** Redirects /event/:token to /event/:token/dashboard */
export function RedirectToEventDashboard() {
  const { token } = useParams<{ token: string }>()
  if (!token) return null
  return <Navigate to={`/event/${token}/dashboard`} replace />
}
