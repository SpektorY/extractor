import { useNavigate } from "react-router-dom"
import { useQuery } from "@tanstack/react-query"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { clearAccessToken, apiRequest } from "@/lib/api"

interface EventItem {
  id: number
  name: string
  address: string
  description: string | null
  created_at: string | null
}

export function AdminDashboard() {
  const navigate = useNavigate()
  const { data: events, isLoading } = useQuery({
    queryKey: ["events"],
    queryFn: () => apiRequest<EventItem[]>("/api/v1/events"),
  })

  function handleLogout() {
    clearAccessToken()
    navigate("/login", { replace: true })
  }

  return (
    <div className="container mx-auto p-6" dir="rtl">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">דאשבורד חמ״ל</h1>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => navigate("/admin/volunteers")}>
            מתנדבים
          </Button>
          <Button onClick={() => navigate("/admin/events/new")}>אירוע חדש</Button>
          <Button variant="outline" onClick={handleLogout}>
            התנתק
          </Button>
        </div>
      </div>

      <section className="mt-8">
        <h2 className="text-lg font-semibold mb-4">אירועים</h2>
        {isLoading && <p className="text-muted-foreground">טוען...</p>}
        {events && events.length === 0 && (
          <p className="text-muted-foreground">אין אירועים. צור אירוע חדש.</p>
        )}
        {events && events.length > 0 && (
          <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {events.map((ev) => (
              <Card
                key={ev.id}
                className="cursor-pointer transition-shadow hover:shadow-md"
                onClick={() => navigate(`/admin/events/${ev.id}`)}
              >
                <CardHeader className="pb-2">
                  <h3 className="font-semibold">{ev.name}</h3>
                </CardHeader>
                <CardContent className="text-sm text-muted-foreground">
                  <p>{ev.address}</p>
                  {ev.created_at && (
                    <p className="mt-1">
                      {new Date(ev.created_at).toLocaleDateString("he-IL")}
                    </p>
                  )}
                  <Button
                    variant="link"
                    className="mt-2 p-0 h-auto"
                    onClick={(e) => {
                      e.stopPropagation()
                      navigate(`/admin/events/${ev.id}`)
                    }}
                  >
                    כניסה לניהול אירוע
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}
