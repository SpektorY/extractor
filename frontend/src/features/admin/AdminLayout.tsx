import { Outlet } from "react-router-dom"

export function AdminLayout() {
  return (
    <div className="min-h-screen bg-background" dir="rtl">
      <Outlet />
    </div>
  )
}
