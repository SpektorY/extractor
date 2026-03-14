import { useState, useEffect } from "react"
import { useParams, useNavigate } from "react-router-dom"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"

const STATUS_OPTIONS = [
  { value: "unchecked", label: "טרם נבחר" },
  { value: "healthy", label: "בריא" },
  { value: "injured", label: "נפגע" },
  { value: "evacuated", label: "פונה לטיפול רפואי" },
  { value: "absent", label: "נעדר" },
]

export function ResidentUpdatePage() {
  const { token, residentId } = useParams<{ token: string; residentId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [status, setStatus] = useState("unchecked")
  const [notes, setNotes] = useState("")

  const rid = residentId ? parseInt(residentId, 10) : NaN

  const { data: residents } = useQuery({
    queryKey: ["volunteer-residents", token],
    queryFn: () =>
      fetch(`${API_BASE}/api/v1/event-by-token/${token}/residents`).then((r) => r.json()),
    enabled: !!token,
  })

  const resident = residents?.find((r: { id: number }) => r.id === rid)

  useEffect(() => {
    if (resident) {
      setStatus(resident.status ?? "unchecked")
      setNotes(resident.volunteer_notes ?? "")
    }
  }, [resident])

  const updateMutation = useMutation({
    mutationFn: () =>
      fetch(`${API_BASE}/api/v1/event-by-token/${token}/residents/${rid}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status, volunteer_notes: notes || null }),
      }).then((r) => {
        if (!r.ok) throw new Error("שגיאה")
        return r.json()
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["volunteer-residents", token] })
      navigate(`/event/${token}/dashboard`, { replace: true })
    },
  })

  if (!token || !resident) {
    return <div className="p-6 text-muted-foreground">טוען או תושב לא נמצא...</div>
  }

  return (
    <div className="p-4" dir="rtl">
      <Card>
        <CardHeader>
          <CardTitle>
            עדכון תושב: {resident.first_name} {resident.last_name}
          </CardTitle>
          <p className="text-muted-foreground">{resident.address}</p>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-2">
            <Label>סטטוס</Label>
            <select
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2"
              value={status}
              onChange={(e) => setStatus(e.target.value)}
            >
              {STATUS_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </div>
          <div className="grid gap-2">
            <Label>הערת מתנדב</Label>
            <Input
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder='למשל "הדלת נעולה"'
            />
          </div>
          <div className="flex gap-2">
            <Button
              onClick={() =>
                updateMutation.mutate(undefined, { onError: () => alert("שגיאה") })
              }
              disabled={updateMutation.isPending}
            >
              שמור סטטוס
            </Button>
            <Button variant="outline" onClick={() => navigate(`/event/${token}/dashboard`)}>
              ביטול
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
