import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { PublicLayout } from "@/features/public/PublicLayout"
import { AdminLayout } from "@/features/admin/AdminLayout"
import { VolunteerLayout } from "@/features/volunteer/VolunteerLayout"
import { ProtectedRoute } from "@/components/ProtectedRoute"
import { LandingPage } from "@/features/public/LandingPage"
import { JoinEventPage } from "@/features/public/JoinEventPage.tsx"
import { VolunteerLoginPage } from "@/features/public/VolunteerLoginPage.tsx"
import { LoginPage } from "@/features/admin/LoginPage"
import { AdminDashboard } from "@/features/admin/AdminDashboard"
import { VolunteersPage } from "@/features/admin/VolunteersPage"
import { CreateEventPage } from "@/features/admin/CreateEventPage"
import { ControlRoomPage } from "@/features/admin/ControlRoomPage"
import { RedirectToEventDashboard } from "@/features/volunteer/RedirectToEventDashboard"
import { VolunteerEventDashboard } from "@/features/volunteer/VolunteerEventDashboard"
import { ResidentUpdatePage } from "@/features/volunteer/ResidentUpdatePage"
import { AddCasualPage } from "@/features/volunteer/AddCasualPage"
import { EventLogPage } from "@/features/volunteer/EventLogPage"

const queryClient = new QueryClient()

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/event/join/:eventId" element={<JoinEventPage />} />
          <Route path="/" element={<PublicLayout />}>
            <Route index element={<LandingPage />} />
            <Route path="login" element={<LoginPage />} />
            <Route path="volunteer-login" element={<VolunteerLoginPage />} />
          </Route>
          <Route
            path="/admin"
            element={
              <ProtectedRoute>
                <AdminLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<AdminDashboard />} />
            <Route path="volunteers" element={<VolunteersPage />} />
            <Route path="events/new" element={<CreateEventPage />} />
            <Route path="events/:eventId" element={<ControlRoomPage />} />
          </Route>
          <Route path="/event/:token" element={<VolunteerLayout />}>
            <Route index element={<RedirectToEventDashboard />} />
            <Route path="dashboard" element={<VolunteerEventDashboard />} />
            <Route path="resident/:residentId" element={<ResidentUpdatePage />} />
            <Route path="casual" element={<AddCasualPage />} />
            <Route path="log" element={<EventLogPage />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App
