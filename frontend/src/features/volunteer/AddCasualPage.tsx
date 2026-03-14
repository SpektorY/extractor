import { useState } from "react"
import { useParams, useNavigate } from "react-router-dom"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"

const STATUS_OPTIONS = [
  { value: "unchecked", label: "טרם נבדק" },
  { value: "healthy", label: "בריא" },
  { value: "injured", label: "נפגע" },
  { value: "evacuated", label: "פונה" },
  { value: "absent", label: "נעדר" },
]

export function AddCasualPage() {
  const { token } = useParams<{ token: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    address: "",
    phone: "",
    status: "unchecked",
    notes: "",
  })

  const mutation = useMutation({
    mutationFn: () =>
      fetch(`${API_BASE}/api/v1/event-by-token/${token}/residents`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          first_name: form.first_name,
          last_name: form.last_name,
          address: form.address,
          phone: form.phone || null,
          status: form.status,
          notes: form.notes || null,
        }),
      }).then((r) => {
        if (!r.ok) throw new Error("שגיאה")
        return r.json()
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["volunteer-residents", token] })
      navigate(`/event/${token}/dashboard`, { replace: true })
    },
  })

  return (
    <div className="container mx-auto max-w-lg p-6" dir="rtl">
      <Card>
        <CardHeader>
          <CardTitle>הוסף מזדמן</CardTitle>
          <p className="text-sm text-muted-foreground">אדם שאותר בשטח ולא ברשימה</p>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-2">
            <Label>שם פרטי (חובה)</Label>
            <Input
              value={form.first_name}
              onChange={(e) => setForm((f) => ({ ...f, first_name: e.target.value }))}
            />
          </div>
          <div className="grid gap-2">
            <Label>שם משפחה (חובה)</Label>
            <Input
              value={form.last_name}
              onChange={(e) => setForm((f) => ({ ...f, last_name: e.target.value }))}
            />
          </div>
          <div className="grid gap-2">
            <Label>כתובת מגורים (חובה)</Label>
            <Input
              value={form.address}
              onChange={(e) => setForm((f) => ({ ...f, address: e.target.value }))}
            />
          </div>
          <div className="grid gap-2">
            <Label>טלפון (רשות)</Label>
            <Input
              value={form.phone}
              onChange={(e) => setForm((f) => ({ ...f, phone: e.target.value }))}
            />
          </div>
          <div className="grid gap-2">
            <Label>סטטוס</Label>
            <select
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2"
              value={form.status}
              onChange={(e) => setForm((f) => ({ ...f, status: e.target.value }))}
            >
              {STATUS_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </div>
          <div className="grid gap-2">
            <Label>הערות</Label>
            <Input
              value={form.notes}
              onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))}
            />
          </div>
          <div className="flex gap-2">
            <Button
              onClick={() =>
                mutation.mutate(undefined, {
                  onError: () => alert("שגיאה"),
                })
              }
              disabled={!form.first_name.trim() || !form.last_name.trim() || !form.address.trim() || mutation.isPending}
            >
              שמור
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
