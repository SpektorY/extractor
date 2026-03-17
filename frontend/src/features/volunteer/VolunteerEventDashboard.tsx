import { useParams, useNavigate } from "react-router-dom"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { useState, useMemo, useCallback, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"

interface EventInfo {
  event_id: number
  event_name: string
  event_address: string
  event_description?: string
  attendance_status?: "coming" | "not_coming" | "arrived" | "left" | null
  volunteer_name?: string | null
}

interface ResidentRow {
  id: number
  first_name: string | null
  last_name: string | null
  address: string
  status: string
  source: string
  volunteer_notes?: string | null
}

const STATUS_OPTIONS = [
  { value: "unchecked", label: "טרם נבחר" },
  { value: "healthy", label: "בריא" },
  { value: "injured", label: "נפגע" },
  { value: "evacuated", label: "פונה" },
  { value: "absent", label: "נעדר" },
] as const

// Order for list: urgent first, then by name
const STATUS_SORT_ORDER: Record<string, number> = {
  unchecked: 0,
  injured: 1,
  absent: 2,
  evacuated: 3,
  healthy: 4,
}

const STATUS_COLOR: Record<string, string> = {
  unchecked: "bg-gray-300",
  healthy: "bg-green-500",
  injured: "bg-red-500",
  evacuated: "bg-orange-500",
  absent: "bg-gray-700",
}

function getDisplayName(r: ResidentRow): string {
  return [r.first_name, r.last_name].filter(Boolean).join(" ") || "—"
}

function getSearchableText(r: ResidentRow): string {
  return `${getDisplayName(r)} ${r.address}`.toLowerCase()
}

export function VolunteerEventDashboard() {
  const { token } = useParams<{ token: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [search, setSearch] = useState("")
  const [editItem, setEditItem] = useState<ResidentRow | null>(null)
  const [editStatus, setEditStatus] = useState<string>("unchecked")
  const [editNotes, setEditNotes] = useState("")

  const attendanceMutation = useMutation({
    mutationFn: async (status: "arrived" | "left") => {
      const r = await fetch(`${API_BASE}/api/v1/event-by-token/${token}/attendance`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status }),
      })
      if (!r.ok) {
        const body = await r.json().catch(() => ({}))
        throw new Error(typeof body.detail === "string" ? body.detail : "שגיאה")
      }
      return r.json() as Promise<{ status: string }>
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["event-by-token", token] })
      queryClient.invalidateQueries({ queryKey: ["volunteer-residents", token] })
    },
  })

  const { data: event, error: eventError } = useQuery({
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

  const { data: residents, isLoading: loadingResidents } = useQuery({
    queryKey: ["volunteer-residents", token],
    queryFn: async () => {
      const r = await fetch(`${API_BASE}/api/v1/event-by-token/${token}/residents`)
      if (!r.ok) throw new Error("שגיאה")
      return r.json() as Promise<ResidentRow[]>
    },
    enabled: !!token && !!event && event.attendance_status === "arrived",
  })

  const updateResidentMutation = useMutation({
    mutationFn: ({ id, status, volunteer_notes }: { id: number; status: string; volunteer_notes: string | null }) =>
      fetch(`${API_BASE}/api/v1/event-by-token/${token}/residents/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status, volunteer_notes }),
      }).then((r) => {
        if (!r.ok) throw new Error("שגיאה")
        return r.json()
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["volunteer-residents", token] })
      setEditItem(null)
    },
  })

  const listItems: ResidentRow[] = useMemo(() => {
    const list = residents ?? []
    return [...list].sort((a, b) => {
      const orderA = STATUS_SORT_ORDER[a.status] ?? 99
      const orderB = STATUS_SORT_ORDER[b.status] ?? 99
      if (orderA !== orderB) return orderA - orderB
      return getDisplayName(a).localeCompare(getDisplayName(b), "he")
    })
  }, [residents])

  const filteredItems = useMemo(() => {
    const q = search.trim().toLowerCase()
    if (!q) return listItems
    return listItems.filter((r) => getSearchableText(r).includes(q))
  }, [listItems, search])

  const openEdit = useCallback((r: ResidentRow) => {
    setEditItem(r)
    setEditStatus(r.status)
    setEditNotes(r.volunteer_notes ?? "")
  }, [])

  const handleSave = useCallback(() => {
    if (!editItem) return
    updateResidentMutation.mutate(
      { id: editItem.id, status: editStatus, volunteer_notes: editNotes.trim() || null },
      { onError: () => alert("שגיאה") }
    )
  }, [editItem, editStatus, editNotes, updateResidentMutation])

  useEffect(() => {
    if (!editItem) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setEditItem(null)
      if (e.key === "Enter" && !e.defaultPrevented) {
        e.preventDefault()
        handleSave()
      }
    }
    window.addEventListener("keydown", onKey)
    return () => window.removeEventListener("keydown", onKey)
  }, [editItem, handleSave])

  const isLoading = loadingResidents
  const isEventEnded = eventError && (eventError as Error & { status?: number }).status === 410

  if (isEventEnded) {
    return (
      <div className="min-h-screen flex items-center justify-center p-6" dir="rtl">
        <Card className="w-full max-w-md">
          <CardContent className="pt-6 text-center">
            <p className="text-muted-foreground text-lg">
              האירוע הסתיים או בוטל. תודה שהתנדבת!
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (!token || !event) return <div className="p-6 text-muted-foreground">טוען...</div>

  if (event.attendance_status === "not_coming") {
    return (
      <div className="min-h-screen flex items-center justify-center p-6" dir="rtl">
        <Card className="w-full max-w-md">
          <CardContent className="pt-6 text-center">
            <p className="text-lg font-medium">תודה על העדכון</p>
            <p className="mt-2 text-muted-foreground">סימנת שאינך מגיע/ה לאירוע.</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (event.attendance_status === "coming" || event.attendance_status === "left") {
    return (
      <div className="min-h-screen flex items-center justify-center p-6" dir="rtl">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle>{event.event_name}</CardTitle>
            <p className="text-muted-foreground">{event.event_address}</p>
          </CardHeader>
          <CardContent className="space-y-4">
            {event.event_description && (
              <p className="text-sm text-muted-foreground">{event.event_description}</p>
            )}
            <p className="text-sm text-muted-foreground">
              {event.attendance_status === "left"
                ? "סימנת שעזבת את האירוע. אם חזרת, אשר/י הגעה מחדש."
                : "יש לאשר הגעה לאירוע לפני כניסה ללוח המתנדבים."}
            </p>
            <Button
              className="h-20 w-full text-lg"
              disabled={attendanceMutation.isPending}
              onClick={() => attendanceMutation.mutate("arrived")}
            >
              הגעתי לאירוע
            </Button>
            {attendanceMutation.isError && (
              <p className="text-sm text-destructive">
                {attendanceMutation.error instanceof Error ? attendanceMutation.error.message : "שגיאה"}
              </p>
            )}
          </CardContent>
        </Card>
      </div>
    )
  }

  if (!event.attendance_status) {
    return (
      <div className="min-h-screen flex items-center justify-center p-6" dir="rtl">
        <Card className="w-full max-w-md">
          <CardContent className="pt-6 text-center">
            <p className="text-muted-foreground">
              יש לאשר הגעה דרך קישור ההצטרפות לפני כניסה ללוח האירוע.
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="min-h-screen" dir="rtl">
      <div className="container mx-auto p-6">
        <Card className="mb-4">
          <CardHeader>
            <CardTitle>{event.event_name}</CardTitle>
            <p className="text-muted-foreground">{event.event_address}</p>
            {event.volunteer_name && (
              <p className="text-sm text-muted-foreground">מתנדב/ת: {event.volunteer_name}</p>
            )}
          </CardHeader>
        </Card>

        <>
          <div className="mb-4 flex flex-wrap gap-2">
            <Button onClick={() => navigate(`/event/${token}/casual`)}>
              הוסף מזדמן +
            </Button>
            <Button variant="outline" onClick={() => navigate(`/event/${token}/log`)}>
              יומן אירוע
            </Button>
            <Button
              variant="destructive"
              onClick={() => {
                if (!window.confirm("לסמן שעזבת את האירוע?")) return
                attendanceMutation.mutate("left")
              }}
              disabled={attendanceMutation.isPending}
            >
              עזבתי את האירוע
            </Button>
          </div>
          <Card>
            <CardHeader>
              <CardTitle>רשימת תושבים</CardTitle>
              <Input
                placeholder="חיפוש לפי שם או כתובת..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="mt-2 max-w-sm"
              />
            </CardHeader>
            <CardContent>
              {isLoading && <p className="text-muted-foreground">טוען...</p>}
              {!isLoading && (
                <ul className="space-y-2">
                  {filteredItems.length === 0 && (
                    <li className="rounded border p-4 text-center text-muted-foreground">
                      {search.trim() ? "אין תוצאות לחיפוש" : "אין תושבים ברשימה"}
                    </li>
                  )}
                  {filteredItems.map((r) => (
                    <li
                      key={r.id}
                      role="button"
                      tabIndex={0}
                      className="flex cursor-pointer items-center gap-2 rounded border p-2 transition-colors hover:bg-muted/50 active:bg-muted"
                      onClick={() => openEdit(r)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" || e.key === " ") {
                          e.preventDefault()
                          openEdit(r)
                        }
                      }}
                    >
                      <span className={`h-3 w-3 flex-shrink-0 rounded-full ${STATUS_COLOR[r.status] ?? "bg-gray-300"}`} />
                      <span className="text-muted-foreground text-xs">{STATUS_OPTIONS.find((opt) => opt.value === r.status)?.label}</span>
                      <span className="text-muted-foreground text-xs">{r.source === "casual" ? "מזדמן" : "תושב"}</span>
                      <span>{getDisplayName(r)}</span>
                      <span className="text-muted-foreground text-sm">— {r.address}</span>
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>
        </>

        {/* Inline update modal — fast flow for danger zone */}
        {editItem && (
          <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
            dir="rtl"
            onClick={() => setEditItem(null)}
            role="dialog"
            aria-modal="true"
          >
            <Card
              className="w-full max-w-md"
              onClick={(e) => e.stopPropagation()}
              onKeyDown={(e) => e.key === "Escape" && setEditItem(null)}
            >
              <CardHeader className="pb-2">
                <CardTitle className="text-lg">{getDisplayName(editItem)}</CardTitle>
                <p className="text-muted-foreground text-sm">{editItem.address}</p>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <p className="mb-2 text-sm font-medium">סטטוס</p>
                  <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
                    {STATUS_OPTIONS.map((opt) => (
                      <Button
                        key={opt.value}
                        type="button"
                        variant={editStatus === opt.value ? "default" : "outline"}
                        size="sm"
                        className="h-auto py-2"
                        onClick={() => setEditStatus(opt.value)}
                      >
                        {opt.label}
                      </Button>
                    ))}
                  </div>
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium">הערות (אופציונלי)</label>
                  <Input
                    value={editNotes}
                    onChange={(e) => setEditNotes(e.target.value)}
                    placeholder="הערה קצרה"
                    className="h-9"
                  />
                </div>
                <div className="flex gap-2">
                  <Button
                    className="flex-1"
                    onClick={handleSave}
                    disabled={updateResidentMutation.isPending}
                  >
                    שמור
                  </Button>
                  <Button variant="outline" onClick={() => setEditItem(null)}>
                    ביטול
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  )
}
