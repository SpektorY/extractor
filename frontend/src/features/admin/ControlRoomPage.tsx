import { useParams, useNavigate, useLocation } from "react-router-dom"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { apiRequest } from "@/lib/api"
import { ShareLinkModal } from "./ShareLinkModal"

const RESIDENTS_FILE_FORMAT = `הקובץ חייב להכיל שורת כותרות ראשונה עם העמודות הבאות (בעברית או באנגלית):
• שם פרטי (חובה)
• שם משפחה (חובה)
• כתובת (חובה)
• טלפון (אופציונלי)
• הערות (אופציונלי)

פורמטים: CSV או Excel (xlsx, xls). קידוד: UTF-8.`

const RESIDENTS_EXAMPLE = [
  ["שם פרטי", "שם משפחה", "כתובת", "טלפון", "הערות"],
  ["משה", "ישראלי", "רחוב הרצל 12 דירה 3", "050-1111111", ""],
  ["רחל", "כהן", "שדרות בן גוריון 5 ב'", "052-2222222", "קשיש"],
]

interface EventDetail {
  id: number
  name: string
  address: string
  description: string | null
}

interface ResidentRow {
  id: number
  first_name: string | null
  last_name: string | null
  address: string
  status: string
  source: string
  volunteer_notes: string | null
  updated_at: string | null
}

interface LogRow {
  id: number
  message: string
  author_type: string
  author_name?: string | null
  created_at: string | null
}

const STATUS_LABELS: Record<string, string> = {
  unchecked: "טרם נבדק",
  healthy: "בריא",
  injured: "נפגע",
  evacuated: "פונה",
  absent: "נעדר",
}

export function ControlRoomPage() {
  const { eventId } = useParams<{ eventId: string }>()
  const id = eventId ? parseInt(eventId, 10) : NaN
  const navigate = useNavigate()
  const location = useLocation()
  const queryClient = useQueryClient()
  const [logMessage, setLogMessage] = useState("")
  const [uploadModalOpen, setUploadModalOpen] = useState(false)
  const [file, setFile] = useState<File | null>(null)
  const [uploadResult, setUploadResult] = useState<{ imported: number; errors: string[] } | null>(null)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState("residents")
  const [shareLinkModalOpen, setShareLinkModalOpen] = useState(false)

  // Live updates: when volunteers update residents/casuals/log, refetch control room data
  useEffect(() => {
    if (!Number.isInteger(id)) return
    const apiBase = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"
    const wsBase = apiBase.replace(/^http/, "ws")
    const token = localStorage.getItem("access_token")
    if (!token) return
    const ws = new WebSocket(`${wsBase}/api/v1/events/${id}/ws?token=${encodeURIComponent(token)}`)
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data?.type === "event_updated") {
          queryClient.invalidateQueries({ queryKey: ["event", id] })
          queryClient.invalidateQueries({ queryKey: ["event-residents", id] })
          queryClient.invalidateQueries({ queryKey: ["event-log", id] })
        }
      } catch {
        // ignore parse errors
      }
    }
    return () => {
      ws.close()
    }
  }, [id, queryClient])

  const { data: event, isLoading: loadingEvent } = useQuery({
    queryKey: ["event", id],
    queryFn: () => apiRequest<EventDetail>(`/api/v1/events/${id}`),
    enabled: Number.isInteger(id),
  })

  // After create event: open share modal and clear state so it doesn’t reopen on refresh
  useEffect(() => {
    const state = location.state as { openShareModal?: boolean } | undefined
    if (event && state?.openShareModal) {
      setShareLinkModalOpen(true)
      navigate(location.pathname, { replace: true, state: {} })
    }
  }, [event, location.state, location.pathname, navigate])

  const { data: residents, isLoading: loadingResidents } = useQuery({
    queryKey: ["event-residents", id],
    queryFn: () => apiRequest<ResidentRow[]>(`/api/v1/events/${id}/residents`),
    enabled: Number.isInteger(id),
  })

  const { data: logEntries } = useQuery({
    queryKey: ["event-log", id],
    queryFn: () => apiRequest<LogRow[]>(`/api/v1/events/${id}/log`),
    enabled: Number.isInteger(id),
  })

  const addLogMutation = useMutation({
    mutationFn: (msg: string) =>
      apiRequest(`/api/v1/events/${id}/log`, {
        method: "POST",
        body: JSON.stringify({ message: msg }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["event-log", id] })
      setLogMessage("")
    },
  })

  async function handleUpload() {
    if (!id || !file) return
    setUploadError(null)
    setUploadResult(null)
    const fd = new FormData()
    fd.append("file", file)
    try {
      const res = await apiRequest<{ imported: number; errors: string[] }>(
        `/api/v1/events/${id}/residents/upload`,
        { method: "POST", body: fd, headers: {} }
      )
      setUploadResult(res)
      queryClient.invalidateQueries({ queryKey: ["event-residents", id] })
    } catch (e) {
      setUploadError(e instanceof Error ? e.message : "שגיאה בהעלאה")
    }
  }

  if (!Number.isInteger(id) || isNaN(id)) {
    return (
      <div className="container mx-auto p-6" dir="rtl">
        <Card>
          <CardContent className="pt-6">
            <p className="text-muted-foreground">מזהה אירוע לא תקין.</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (loadingEvent || !event) {
    return <div className="container mx-auto p-6 text-muted-foreground">טוען...</div>
  }

  return (
    <div className="container mx-auto p-6" dir="rtl">
      <div className="flex items-center justify-between">
        <div>
          <Button variant="ghost" onClick={() => navigate("/admin")}>
            חזרה לדאשבורד
          </Button>
          <h1 className="text-2xl font-bold mt-2">{event.name}</h1>
          <p className="text-muted-foreground">{event.address}</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Button variant="outline" onClick={() => setShareLinkModalOpen(true)}>
            קישור לאירוע
          </Button>
          <Button variant="outline" onClick={() => setUploadModalOpen(true)}>
            העלאת קובץ תושבים
          </Button>
          <Button
            variant="outline"
            onClick={() => {
              const base = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"
              const token = localStorage.getItem("access_token")
              fetch(`${base}/api/v1/events/${id}/export-excel`, {
                headers: token ? { Authorization: `Bearer ${token}` } : {},
              })
                .then((r) => (r.ok ? r.blob() : Promise.reject(new Error("שגיאה"))))
                .then((blob) => {
                  const a = document.createElement("a")
                  a.href = URL.createObjectURL(blob)
                  a.download = `event-${id}.xlsx`
                  a.click()
                })
                .catch(() => alert("שגיאה בהורדה"))
            }}
          >
            הורד דוח אקסל
          </Button>
          <Button
            variant="destructive"
            className="ms-2"
            onClick={async () => {
              if (!confirm("למחוק את האירוע? רשימת התושבים והדיווחים יימחקו. רשימת המתנדבים הכללית לא תימחק.")) return
              try {
                await apiRequest(`/api/v1/events/${id}`, { method: "DELETE" })
                queryClient.invalidateQueries({ queryKey: ["events"] })
                navigate("/admin", { replace: true })
              } catch (e) {
                alert(e instanceof Error ? e.message : "שגיאה")
              }
            }}
          >
            מחק אירוע
          </Button>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="mt-6">
        <TabsList>
          <TabsTrigger value="residents">תושבים</TabsTrigger>
          <TabsTrigger value="log">יומן אירוע</TabsTrigger>
        </TabsList>
        <TabsContent value="residents">
          <Card>
            <CardHeader>
              <CardTitle>רשימת תושבים</CardTitle>
            </CardHeader>
            <CardContent>
              {loadingResidents && <p className="text-muted-foreground">טוען...</p>}
              {residents != null && residents.length === 0 && (
                <p className="text-sm text-muted-foreground py-6 text-center">
                  אין תושבים ברשימה. העלה קובץ או ביקש ממתנדבים להוסיף מזדמנים.
                </p>
              )}
              {residents != null && residents.length > 0 && (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>סוג</TableHead>
                      <TableHead>שם</TableHead>
                      <TableHead>כתובת</TableHead>
                      <TableHead>סטטוס</TableHead>
                      <TableHead>הערות</TableHead>
                      <TableHead>עודכן</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {residents.map((r) => (
                      <TableRow key={r.id}>
                        <TableCell>{r.source === "casual" ? "מזדמן" : "תושב"}</TableCell>
                        <TableCell>
                          {[r.first_name, r.last_name].filter(Boolean).join(" ") || "—"}
                        </TableCell>
                        <TableCell>{r.address}</TableCell>
                        <TableCell>{STATUS_LABELS[r.status] ?? r.status}</TableCell>
                        <TableCell>{r.volunteer_notes ?? "—"}</TableCell>
                        <TableCell>{r.updated_at ? new Date(r.updated_at).toLocaleString("he-IL") : "—"}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="log">
          <Card>
            <CardHeader>
              <CardTitle>יומן אירוע / צ׳אט</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 max-h-64 overflow-auto border rounded p-2">
                {!logEntries?.length ? (
                  <p className="text-sm text-muted-foreground text-center py-6">אין הודעות ביומן עדיין</p>
                ) : (
                  logEntries.map((e) => (
                    <div key={e.id} className="text-sm">
                      <span className="text-muted-foreground">
                        {e.created_at ? new Date(e.created_at).toLocaleString("he-IL") : ""}{" "}
                        {e.author_name ? `(${e.author_name})` : `[${e.author_type}]`}
                      </span>{" "}
                      {e.message}
                    </div>
                  ))
                )}
              </div>
              <div className="flex gap-2 mt-2">
                <Input
                  placeholder="הודעה לכלל המתנדבים"
                  value={logMessage}
                  onChange={(e) => setLogMessage(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && addLogMutation.mutate(logMessage)}
                />
                <Button
                  onClick={() => addLogMutation.mutate(logMessage)}
                  disabled={!logMessage.trim() || addLogMutation.isPending}
                >
                  שלח
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Upload residents modal */}
      {uploadModalOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
          dir="rtl"
          onClick={() => setUploadModalOpen(false)}
          onKeyDown={(e) => e.key === "Escape" && setUploadModalOpen(false)}
          role="dialog"
          aria-modal="true"
        >
          <Card className="mx-4 w-full max-w-lg max-h-[90vh] flex flex-col" onClick={(e) => e.stopPropagation()}>
            <CardHeader className="flex-shrink-0">
              <CardTitle>העלאת קובץ תושבים</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 overflow-auto flex-1">
              <div className="rounded border bg-muted/30 p-3 text-sm whitespace-pre-wrap">
                {RESIDENTS_FILE_FORMAT}
              </div>
              <div className="text-sm font-medium">דוגמה (שורת כותרות + שורות נתונים):</div>
              <div className="overflow-x-auto border rounded text-sm">
                <table className="w-full border-collapse">
                  <tbody>
                    {RESIDENTS_EXAMPLE.map((row, i) => (
                      <tr key={i}>
                        {row.map((cell, j) => (
                          <td key={j} className="border px-2 py-1">
                            {cell || "—"}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="flex gap-2 items-center">
                <Input
                  type="file"
                  accept=".xlsx,.xls,.csv"
                  onChange={(e) => {
                    setFile(e.target.files?.[0] ?? null)
                    setUploadError(null)
                    setUploadResult(null)
                  }}
                />
                <Button onClick={handleUpload} disabled={!file}>
                  העלה
                </Button>
              </div>
              {uploadError && (
                <div className="rounded border border-destructive bg-destructive/10 p-3 text-sm text-destructive">
                  <p className="font-medium">שגיאה בהעלאה</p>
                  <p className="mt-1">{uploadError}</p>
                  <p className="mt-2 text-muted-foreground">{RESIDENTS_FILE_FORMAT}</p>
                </div>
              )}
              {uploadResult && (
                <div className="rounded border bg-muted/30 p-3 text-sm">
                  <p className="text-green-600 font-medium">נטענו {uploadResult.imported} תושבים.</p>
                  {uploadResult.errors.length > 0 && (
                    <>
                      <p className="mt-1 text-amber-600">שגיאות בשורות: {uploadResult.errors.length}</p>
                      <ul className="mt-1 list-disc list-inside text-muted-foreground max-h-24 overflow-auto">
                        {uploadResult.errors.slice(0, 10).map((err, i) => (
                          <li key={i}>{err}</li>
                        ))}
                        {uploadResult.errors.length > 10 && (
                          <li>... ועוד {uploadResult.errors.length - 10} שגיאות</li>
                        )}
                      </ul>
                      <p className="mt-2 text-xs text-muted-foreground">תקן את השורות בקובץ והעלה שוב. {RESIDENTS_FILE_FORMAT}</p>
                    </>
                  )}
                </div>
              )}
              <Button variant="outline" className="w-full" onClick={() => setUploadModalOpen(false)}>
                סגור
              </Button>
            </CardContent>
          </Card>
        </div>
      )}

      {shareLinkModalOpen && (
        <ShareLinkModal
          joinUrl={`${window.location.origin}/event/join/${id}`}
          onClose={() => setShareLinkModalOpen(false)}
        />
      )}
    </div>
  )
}
