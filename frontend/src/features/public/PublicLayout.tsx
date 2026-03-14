import { Outlet } from "react-router-dom"

export function PublicLayout() {
  return (
    <div className="min-h-screen bg-background" dir="rtl">
      <Outlet />
    </div>
  )
}
