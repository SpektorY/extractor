import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { apiRequest } from "@/lib/api"

export function CreateEventPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [form, setForm] = useState({ name: "", address: "", description: "" })

  const createMutation = useMutation({
    mutationFn: () =>
      apiRequest<{ id: number }>("/api/v1/events", {
        method: "POST",
        body: JSON.stringify(form),
      }),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["events"] })
      navigate(`/admin/events/${data.id}`, { replace: true })
    },
  })

  return (
    <div className="container mx-auto max-w-2xl p-6" dir="rtl">
      <Button variant="ghost" onClick={() => navigate("/admin")}>
        חזרה לדאשבורד
      </Button>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle>אירוע חדש</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid gap-4">
            <div className="grid gap-2">
              <Label>שם אירוע</Label>
              <Input
                value={form.name}
                onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                placeholder='למשל "נפילה ברחוב הרצל"'
              />
            </div>
            <div className="grid gap-2">
              <Label>כתובת</Label>
              <Input
                value={form.address}
                onChange={(e) => setForm((f) => ({ ...f, address: e.target.value }))}
              />
            </div>
            <div className="grid gap-2">
              <Label>תיאור (אופציונלי)</Label>
              <Input
                value={form.description}
                onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
              />
            </div>
            <Button
              onClick={() =>
                createMutation.mutate(undefined, {
                  onError: (e) => alert(e instanceof Error ? e.message : "שגיאה"),
                })
              }
              disabled={!form.name || !form.address || createMutation.isPending}
            >
              צור אירוע
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
