import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { apiRequest } from "@/lib/api"

interface VolunteerItem {
  id: number
  first_name: string
  last_name: string
  phone: string
  group_tag: string | null
  living_area: string | null
  anonymized: boolean
  status: "pending" | "approved"
  deleted_at: string | null
}

type ConfirmAction = "delete" | "anonymize"
type ViewFilter = "active" | "history" // active = only current volunteers; history = include removed & anonymized

export function VolunteersPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [addOpen, setAddOpen] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [form, setForm] = useState({ first_name: "", last_name: "", phone: "", group_tag: "", living_area: "" })
  const [formError, setFormError] = useState<string | null>(null)
  const [confirmModal, setConfirmModal] = useState<{ action: ConfirmAction; volunteer: VolunteerItem } | null>(null)
  const [viewFilter, setViewFilter] = useState<ViewFilter>("active")
  const [importModalOpen, setImportModalOpen] = useState(false)
  const [importFile, setImportFile] = useState<File | null>(null)
  const [importResult, setImportResult] = useState<{ imported: number; errors: string[] } | null>(null)
  const [importError, setImportError] = useState<string | null>(null)

  const { data: allVolunteers, isLoading } = useQuery({
    queryKey: ["volunteers"],
    queryFn: () =>
      apiRequest<VolunteerItem[]>(`/api/v1/volunteers?include_deleted=true`),
  })

  const volunteers =
    viewFilter === "active" && allVolunteers
      ? allVolunteers.filter((v) => !v.deleted_at && !v.anonymized)
      : allVolunteers ?? []

  const createMutation = useMutation({
    mutationFn: (body: typeof form) =>
      apiRequest("/api/v1/volunteers", {
        method: "POST",
        body: JSON.stringify({
          first_name: body.first_name,
          last_name: body.last_name,
          phone: body.phone,
          group_tag: body.group_tag || null,
          living_area: body.living_area || null,
        }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["volunteers"] })
      setAddOpen(false)
      setFormError(null)
      setForm({ first_name: "", last_name: "", phone: "", group_tag: "", living_area: "" })
    },
    onError: (e) => {
      setFormError(e instanceof Error ? e.message : "שגיאה")
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, body }: { id: number; body: typeof form }) =>
      apiRequest(`/api/v1/volunteers/${id}`, {
        method: "PATCH",
        body: JSON.stringify({
          first_name: body.first_name,
          last_name: body.last_name,
          phone: body.phone,
          group_tag: body.group_tag || null,
          living_area: body.living_area || null,
        }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["volunteers"] })
      setEditingId(null)
      setFormError(null)
      setForm({ first_name: "", last_name: "", phone: "", group_tag: "", living_area: "" })
    },
    onError: (e) => {
      setFormError(e instanceof Error ? e.message : "שגיאה")
    },
  })

  const approveMutation = useMutation({
    mutationFn: (id: number) => apiRequest(`/api/v1/volunteers/${id}/approve`, { method: "POST" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["volunteers"] })
    },
  })

  async function handleImport() {
    if (!importFile) return
    setImportError(null)
    setImportResult(null)
    const fd = new FormData()
    fd.append("file", importFile)
    try {
      const res = await apiRequest<{ imported: number; errors: string[] }>(
        "/api/v1/volunteers/import",
        { method: "POST", body: fd, headers: {} }
      )
      setImportResult(res)
      queryClient.invalidateQueries({ queryKey: ["volunteers"] })
    } catch (e) {
      setImportError(e instanceof Error ? e.message : "שגיאה בהעלאה")
    }
  }

  function openEdit(v: VolunteerItem) {
    setEditingId(v.id)
    setFormError(null)
    setForm({
      first_name: v.first_name,
      last_name: v.last_name,
      phone: v.phone,
      group_tag: v.group_tag ?? "",
      living_area: v.living_area ?? "",
    })
  }

  function openConfirmDelete(v: VolunteerItem) {
    setConfirmModal({ action: "delete", volunteer: v })
  }

  function openConfirmAnonymize(v: VolunteerItem) {
    setConfirmModal({ action: "anonymize", volunteer: v })
  }

  async function confirmAction() {
    if (!confirmModal) return
    const { action, volunteer } = confirmModal
    setConfirmModal(null)
    if (action === "delete") {
      await apiRequest(`/api/v1/volunteers/${volunteer.id}`, { method: "DELETE" })
    } else {
      await apiRequest(`/api/v1/volunteers/${volunteer.id}/anonymize`, { method: "POST" })
    }
    queryClient.invalidateQueries({ queryKey: ["volunteers"] })
  }

  return (
    <div className="container mx-auto p-6" dir="rtl">
      <div className="flex items-center justify-between">
        <Button variant="ghost" onClick={() => navigate("/admin")}>
          חזרה לדאשבורד
        </Button>
      </div>
      <Card className="mt-6">
        <CardHeader>
          <CardTitle>ניהול מתנדבים</CardTitle>
          <div className="flex flex-wrap items-center gap-2 pt-2">
            <Button onClick={() => setAddOpen(true)}>הוסף מתנדב</Button>
            <Button variant="outline" onClick={() => setImportModalOpen(true)}>
              ייבוא מתנדבים מקובץ
            </Button>
            <Button
              variant={viewFilter === "active" ? "outline" : "secondary"}
              size="sm"
              onClick={() => setViewFilter(viewFilter === "active" ? "history" : "active")}
            >
              {viewFilter === "active" ? "הצג כל המתנדבים" : "הצג מתנדבים פעילים בלבד"}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {addOpen && (
            <Card className="mb-6 border-dashed">
              <CardHeader>
                <CardTitle>מתנדב חדש</CardTitle>
                <p className="text-sm text-muted-foreground">מתנדבים שנוספו על ידי מנהל מקבלים סטטוס מאושר אוטומטית.</p>
              </CardHeader>
              <CardContent className="grid gap-4 sm:grid-cols-2">
                <div className="grid gap-2">
                  <Label>שם פרטי</Label>
                  <Input
                    value={form.first_name}
                    onChange={(e) => setForm((f) => ({ ...f, first_name: e.target.value }))}
                  />
                </div>
                <div className="grid gap-2">
                  <Label>שם משפחה</Label>
                  <Input
                    value={form.last_name}
                    onChange={(e) => setForm((f) => ({ ...f, last_name: e.target.value }))}
                  />
                </div>
                <div className="grid gap-2">
                  <Label>טלפון</Label>
                  <Input
                    value={form.phone}
                    onChange={(e) => setForm((f) => ({ ...f, phone: e.target.value }))}
                  />
                </div>
                <div className="grid gap-2">
                  <Label>אזור מגורים</Label>
                  <Input
                    value={form.living_area}
                    onChange={(e) => setForm((f) => ({ ...f, living_area: e.target.value }))}
                  />
                </div>
                <div className="grid gap-2">
                  <Label>קבוצה / התמחות</Label>
                  <Input
                    value={form.group_tag}
                    onChange={(e) => setForm((f) => ({ ...f, group_tag: e.target.value }))}
                  />
                </div>
                {formError && <p className="text-sm text-destructive sm:col-span-2">{formError}</p>}
                <div className="flex gap-2 sm:col-span-2">
                  <Button
                    onClick={() => createMutation.mutate(form)}
                    disabled={!form.first_name || !form.last_name || !form.phone || createMutation.isPending}
                  >
                    שמור
                  </Button>
                  <Button variant="outline" onClick={() => { setAddOpen(false); setFormError(null) }}>
                    ביטול
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
          {editingId !== null && (
            <Card className="mb-6 border-dashed">
              <CardHeader>
                <CardTitle>עריכת מתנדב</CardTitle>
              </CardHeader>
              <CardContent className="grid gap-4 sm:grid-cols-2">
                <div className="grid gap-2">
                  <Label>שם פרטי</Label>
                  <Input
                    value={form.first_name}
                    onChange={(e) => setForm((f) => ({ ...f, first_name: e.target.value }))}
                  />
                </div>
                <div className="grid gap-2">
                  <Label>שם משפחה</Label>
                  <Input
                    value={form.last_name}
                    onChange={(e) => setForm((f) => ({ ...f, last_name: e.target.value }))}
                  />
                </div>
                <div className="grid gap-2">
                  <Label>טלפון</Label>
                  <Input
                    value={form.phone}
                    onChange={(e) => setForm((f) => ({ ...f, phone: e.target.value }))}
                  />
                </div>
                <div className="grid gap-2">
                  <Label>אזור מגורים</Label>
                  <Input
                    value={form.living_area}
                    onChange={(e) => setForm((f) => ({ ...f, living_area: e.target.value }))}
                  />
                </div>
                <div className="grid gap-2">
                  <Label>קבוצה / התמחות</Label>
                  <Input
                    value={form.group_tag}
                    onChange={(e) => setForm((f) => ({ ...f, group_tag: e.target.value }))}
                  />
                </div>
                {formError && <p className="text-sm text-destructive sm:col-span-2">{formError}</p>}
                <div className="flex gap-2 sm:col-span-2">
                  <Button
                    onClick={() => updateMutation.mutate({ id: editingId, body: form })}
                    disabled={!form.first_name || !form.last_name || !form.phone || updateMutation.isPending}
                  >
                    שמור שינויים
                  </Button>
                  <Button variant="outline" onClick={() => { setEditingId(null); setFormError(null); setForm({ first_name: "", last_name: "", phone: "", group_tag: "", living_area: "" }) }}>
                    ביטול
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
          {isLoading && <p className="text-muted-foreground">טוען...</p>}
          {!isLoading && volunteers.length === 0 && (
            <p className="text-sm text-muted-foreground py-6 text-center">
              אין מתנדבים. הוסף מתנדב עם הכפתור למעלה.
            </p>
          )}
          {volunteers.length > 0 && (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>שם</TableHead>
                  <TableHead>טלפון</TableHead>
                  <TableHead>אזור</TableHead>
                  <TableHead>קבוצה</TableHead>
                  <TableHead>סטטוס הרשאה</TableHead>
                  <TableHead>פעולות</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {volunteers.map((v) => (
                  <TableRow key={v.id}>
                    <TableCell>
                      {v.first_name} {v.last_name}
                      {v.anonymized && " (אנונימי)"}
                    </TableCell>
                    <TableCell>{v.anonymized ? "—" : v.phone}</TableCell>
                    <TableCell>{v.living_area ?? "—"}</TableCell>
                    <TableCell>{v.group_tag ?? "—"}</TableCell>
                    <TableCell>
                      {v.status === "approved" ? "מאושר" : "ממתין לאישור"}
                    </TableCell>
                    <TableCell className="space-x-2 space-x-reverse">
                      {!v.anonymized && !v.deleted_at && (
                        <>
                          {v.status === "pending" && (
                            <Button
                              variant="default"
                              size="sm"
                              onClick={() => approveMutation.mutate(v.id)}
                              disabled={approveMutation.isPending}
                            >
                              אשר
                            </Button>
                          )}
                          <Button
                            variant="outline"
                            size="sm"
                            className="ml-2"
                            onClick={() => openEdit(v)}
                          >
                            ערוך
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => openConfirmDelete(v)}
                          >
                            מחק
                          </Button>
                        </>
                      )}
                      {!v.anonymized && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => openConfirmAnonymize(v)}
                        >
                          אנונימיזציה
                        </Button>
                      )}
                      {v.anonymized && <span className="text-muted-foreground">הוסר (אנונימי)</span>}
                      {v.deleted_at && !v.anonymized && <span className="text-muted-foreground">הוסר</span>}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {importModalOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
          dir="rtl"
          onClick={() => setImportModalOpen(false)}
          onKeyDown={(e) => e.key === "Escape" && setImportModalOpen(false)}
          role="dialog"
          aria-modal="true"
        >
          <Card className="mx-4 w-full max-w-lg" onClick={(e) => e.stopPropagation()}>
            <CardHeader>
              <CardTitle>ייבוא מתנדבים</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-muted-foreground">
                פורמט נתמך: CSV או Excel עם עמודות first_name, last_name, phone (אופציונלי: group_tag, living_area).
              </p>
              <Input
                type="file"
                accept=".xlsx,.xls,.csv"
                onChange={(e) => {
                  setImportFile(e.target.files?.[0] ?? null)
                  setImportError(null)
                  setImportResult(null)
                }}
              />
              <Button onClick={handleImport} disabled={!importFile}>
                העלה
              </Button>
              {importError && (
                <p className="text-sm text-destructive">{importError}</p>
              )}
              {importResult && (
                <div className="rounded border bg-muted/30 p-3 text-sm">
                  <p className="font-medium text-green-600">נוספו {importResult.imported} מתנדבים.</p>
                  {importResult.errors.length > 0 && (
                    <>
                      <p className="mt-1 text-amber-600">שגיאות: {importResult.errors.length}</p>
                      <ul className="mt-1 list-disc list-inside text-muted-foreground max-h-24 overflow-auto">
                        {importResult.errors.slice(0, 10).map((err, i) => (
                          <li key={i}>{err}</li>
                        ))}
                      </ul>
                    </>
                  )}
                </div>
              )}
              <Button variant="outline" className="w-full" onClick={() => setImportModalOpen(false)}>
                סגור
              </Button>
            </CardContent>
          </Card>
        </div>
      )}

      {confirmModal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
          dir="rtl"
          onClick={() => setConfirmModal(null)}
          onKeyDown={(e) => e.key === "Escape" && setConfirmModal(null)}
          role="dialog"
          aria-modal="true"
        >
          <Card className="mx-4 w-full max-w-md" onClick={(e) => e.stopPropagation()}>
            <CardHeader>
              <CardTitle>
                {confirmModal.action === "delete" ? "מחיקת מתנדב" : "אנונימיזציה"}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-muted-foreground">
                {confirmModal.action === "delete"
                  ? "מחיקה – המתנדב יוסר מהרשימה."
                  : "אנונימיזציה – פרטי המתנדב יוחלפו בפרטים אנונימיים."}
              </p>
              <p className="font-medium">
                {confirmModal.volunteer.first_name} {confirmModal.volunteer.last_name}
              </p>
              <div className="flex gap-2">
                <Button variant="destructive" onClick={confirmAction}>
                  {confirmModal.action === "delete" ? "מחק" : "אנונימיזציה"}
                </Button>
                <Button variant="outline" onClick={() => setConfirmModal(null)}>
                  ביטול
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
