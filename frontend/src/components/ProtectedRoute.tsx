import { Navigate, useLocation } from "react-router-dom"

const getToken = (): string | null => localStorage.getItem("access_token")

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const location = useLocation()
  if (!getToken()) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }
  return <>{children}</>
}
