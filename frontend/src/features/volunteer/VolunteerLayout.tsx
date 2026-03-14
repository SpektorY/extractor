import { Outlet } from "react-router-dom"

export function VolunteerLayout() {
  return (
    <div className="min-h-screen bg-background" dir="rtl">
      <Outlet />
    </div>
  )
}
