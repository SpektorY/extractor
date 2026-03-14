import { useState } from "react"
import { useParams, useNavigate } from "react-router-dom"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"

interface LogEntry {
  id: number
  message: string
  author_type: string
  created_at: string | null
}

export function EventLogPage() {
  const { token } = useParams<{ token: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [message, setMessage] = useState("")

  const { data: logEntries } = useQuery({
    queryKey: ["event-log-vol", token],
    queryFn: () =>
      fetch(`${API_BASE}/api/v1/event-by-token/${token}/log`).then((r) => r.json() as Promise<LogEntry[]>),
    enabled: !!token,
  })

  const addMutation = useMutation({
    mutationFn: (msg: string) =>
      fetch(`${API_BASE}/api/v1/event-by-token/${token}/log`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msg }),
      }).then((r) => {
        if (!r.ok) throw new Error("שגיאה")
        return r.json()
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["event-log-vol", token] })
      setMessage("")
    },
  })

  return (
    <div className="container mx-auto max-w-2xl p-6" dir="rtl">
      <Button variant="ghost" onClick={() => navigate(`/event/${token}/dashboard`)}>
        חזרה
      </Button>
      <Card className="mt-4">
        <CardHeader>
          <CardTitle>יומן אירוע / צ׳אט צוות</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 max-h-80 overflow-auto border rounded p-2 mb-4">
            {logEntries?.map((e) => (
              <div key={e.id} className="text-sm">
                <span className="text-muted-foreground">
                  {e.created_at ? new Date(e.created_at).toLocaleString("he-IL") : ""} [{e.author_type}]
                </span>{" "}
                {e.message}
              </div>
            ))}
          </div>
          <div className="flex gap-2">
            <Input
              placeholder="הודעה כללית (למשל: סורק קומה 2)"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && addMutation.mutate(message)}
            />
            <Button
              onClick={() => addMutation.mutate(message)}
              disabled={!message.trim() || addMutation.isPending}
            >
              שלח
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
