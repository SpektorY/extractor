import { useState } from "react"
import { useParams, useNavigate } from "react-router-dom"
import { useQuery, useMutation } from "@tanstack/react-query"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"

interface EventInfo {
  event_id: number
  event_name: string
  event_address: string
  event_description: string
}

export function EventGatePage() {
  const { token } = useParams<{ token: string }>()
  const navigate = useNavigate()
  const [declined, setDeclined] = useState(false)

  const { data: event, isLoading, error } = useQuery({
    queryKey: ["event-by-token", token],
    queryFn: async () => {
      const r = await fetch(`${API_BASE}/api/v1/event-by-token/${token}`)
      if (!r.ok) {
        const body = await r.json().catch(() => ({}))
        const err = new Error(typeof body.detail === "string" ? body.detail : "קישור לא תקין") as Error & { status?: number }
        err.status = r.status
        throw err
      }
      return r.json() as Promise<EventInfo>
    },
    enabled: !!token,
  })

  const respondMutation = useMutation({
    mutationFn: (coming: boolean) =>
      fetch(`${API_BASE}/api/v1/event-by-token/${token}/respond`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ coming }),
      }).then((r) => {
        if (!r.ok) throw new Error("שגיאה")
        return r.json()
      }),
    onSuccess: (_, coming) => {
      if (coming) {
        navigate(`/event/${token}/dashboard`, { replace: true })
      } else {
        setDeclined(true)
      }
    },
  })

  if (!token) return <div className="p-6">חסר קישור</div>
  const isEventEnded = error && (error as Error & { status?: number }).status === 410
  if (error || (!isLoading && !event)) {
    return (
      <div className="flex min-h-screen items-center justify-center p-6" dir="rtl">
        <Card className="w-full max-w-sm">
          <CardContent className="pt-6">
            {isEventEnded ? (
              <p className="text-center text-muted-foreground">
                האירוע הסתיים או בוטל. תודה שהתנדבת!
              </p>
            ) : (
              <p className="text-center text-destructive">קישור לא תקין או שפג תוקפו.</p>
            )}
          </CardContent>
        </Card>
      </div>
    )
  }
  if (isLoading || !event) {
    return <div className="flex min-h-screen items-center justify-center p-6 text-muted-foreground">טוען...</div>
  }

  if (declined) {
    return (
      <div className="flex min-h-screen items-center justify-center p-6" dir="rtl">
        <Card className="w-full max-w-md">
          <CardContent className="pt-6 text-center">
            <p className="text-lg">תודה! עדכנו שלא תגיע.</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-6" dir="rtl">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>{event.event_name}</CardTitle>
          <p className="text-muted-foreground">{event.event_address}</p>
          {event.event_description && (
            <p className="text-muted-foreground">{event.event_description}</p>
          )}
        </CardHeader>
        <CardContent className="grid gap-4">
          <p className="text-center">האם באפשרותך לסייע?</p>
          <div className="grid grid-cols-2 gap-4">
            <Button
              size="lg"
              className="h-20 text-lg"
              onClick={() =>
                respondMutation.mutate(true, {
                  onError: () => alert("שגיאה. נסה שוב."),
                })
              }
              disabled={respondMutation.isPending}
            >
              מגיע
            </Button>
            <Button
              size="lg"
              variant="outline"
              className="h-20 text-lg"
              onClick={() =>
                respondMutation.mutate(false, {
                  onSuccess: () => { },
                  onError: () => alert("שגיאה."),
                })
              }
              disabled={respondMutation.isPending}
            >
              לא מגיע
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
