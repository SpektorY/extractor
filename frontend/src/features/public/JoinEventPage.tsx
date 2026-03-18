import { useEffect, useState } from "react"
import { useMutation, useQuery } from "@tanstack/react-query"
import { useNavigate, useParams } from "react-router-dom"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { hasVolunteerToken, volunteerApiRequest } from "@/lib/api"

interface EventPublic {
  id: number
  name: string
  address: string
  description?: string | null
}

interface VolunteerMe {
  id: number
  first_name: string
  last_name: string
  status: "pending" | "approved"
}

type AttendanceStatus = "coming" | "not_coming" | "arrived" | "left"

interface JoinResponse {
  magic_token: string
  attendance_status?: AttendanceStatus | null
}

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"

export function JoinEventPage() {
  const { eventId } = useParams<{ eventId: string }>()
  const navigate = useNavigate()
  const id = eventId ? parseInt(eventId, 10) : NaN
  const [step, setStep] = useState<"response" | "arrival" | "thank_you">("response")
  const [eventToken, setEventToken] = useState<string | null>(null)
  const [pendingError, setPendingError] = useState<string | null>(null)

  useEffect(() => {
    if (!Number.isInteger(id)) return
    if (!hasVolunteerToken()) {
      navigate("/volunteer-login", { replace: true, state: { returnTo: `/event/join/${id}` } })
    }
  }, [id, navigate])

  const { data: event, isLoading: loadingEvent, error: eventError } = useQuery({
    queryKey: ["public-event", id],
    queryFn: () => volunteerApiRequest<EventPublic>(`/api/v1/public/event/${id}`),
    enabled: Number.isInteger(id),
  })

  const meQuery = useQuery({
    queryKey: ["volunteer-me"],
    queryFn: () => volunteerApiRequest<VolunteerMe>("/api/v1/public/auth/me"),
    enabled: Number.isInteger(id) && hasVolunteerToken(),
    retry: false,
  })

  useEffect(() => {
    if (!meQuery.error) return
    navigate("/volunteer-login", { replace: true, state: { returnTo: `/event/join/${id}` } })
  }, [id, meQuery.error, navigate])

  const joinMutation = useMutation({
    mutationFn: () =>
      volunteerApiRequest<JoinResponse>(`/api/v1/public/event/${id}/join`, {
        method: "POST",
        body: JSON.stringify({}),
      }),
    onSuccess: (data) => {
      setEventToken(data.magic_token)
      if (data.attendance_status === "arrived") {
        navigate(`/event/${data.magic_token}`, { replace: true })
        return
      }
      if (data.attendance_status === "not_coming") {
        setStep("response")
        return
      }
      if (data.attendance_status === "coming" || data.attendance_status === "left") {
        setStep("arrival")
        return
      }
      setStep("response")
    },
    onError: (e) => {
      setPendingError(e instanceof Error ? e.message : "שגיאה")
    },
  })

  const attendanceMutation = useMutation({
    mutationFn: async (status: AttendanceStatus) => {
      if (!eventToken) throw new Error("קישור האירוע לא זמין")
      const res = await fetch(`${API_BASE}/api/v1/event-by-token/${eventToken}/attendance`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(typeof err.detail === "string" ? err.detail : "שגיאה")
      }
      return res.json() as Promise<{ status: AttendanceStatus }>
    },
  })

  useEffect(() => {
    if (meQuery.data?.status !== "approved") return
    if (!joinMutation.isPending && !joinMutation.data && !joinMutation.error) {
      joinMutation.mutate()
    }
  }, [joinMutation, meQuery.data, meQuery.error])

  function handleAttendanceChoice(status: AttendanceStatus) {
    attendanceMutation.mutate(status, {
      onSuccess: () => {
        if (status === "not_coming") {
          setStep("thank_you")
          return
        }
        if (status === "coming") {
          setStep("arrival")
          return
        }
        if (status === "arrived" && eventToken) {
          navigate(`/event/${eventToken}`, { replace: true })
        }
      },
    })
  }

  if (!Number.isInteger(id)) {
    return (
      <div className="flex min-h-screen items-center justify-center p-6" dir="rtl">
        <Card className="w-full max-w-sm">
          <CardContent className="pt-6">
            <p className="text-center text-muted-foreground">קישור לא תקין.</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (loadingEvent || meQuery.isLoading || joinMutation.isPending) {
    return <div className="flex min-h-screen items-center justify-center p-6 text-muted-foreground" dir="rtl">טוען...</div>
  }

  if (eventError || !event || meQuery.error) {
    return (
      <div className="flex min-h-screen items-center justify-center p-6" dir="rtl">
        <Card className="w-full max-w-sm">
          <CardContent className="pt-6">
            <p className="text-center text-destructive">אירוע לא נמצא או שנדרשת התחברות מחדש.</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (meQuery.data?.status === "pending") {
    return (
      <div className="flex min-h-screen items-center justify-center p-6" dir="rtl">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle>החשבון ממתין לאישור</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <p>נרשמת בהצלחה, מנהל חמ״ל צריך לאשר אותך לפני כניסה לאירוע.</p>
            <p className="text-muted-foreground">אחרי אישור תקבל/י SMS ותוכל/י להמשיך.</p>
            {pendingError && <p className="text-destructive">{pendingError}</p>}
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-6" dir="rtl">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>הצטרפות לאירוע: {event.name}</CardTitle>
          <p className="text-sm text-muted-foreground">
            {step === "response" && "האם את/ה מגיע/ה לאירוע?"}
            {step === "arrival" && "כשתגיע/י לאירוע, אשר/י הגעה כדי להיכנס ללוח המתנדבים."}
            {step === "thank_you" && "תודה שעדכנת אותנו."}
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          {step === "response" && (
            <div className="grid gap-4">
              <div className="rounded-lg border bg-muted/30 p-4 text-sm">
                <p className="font-medium">{event.name}</p>
                <p className="text-muted-foreground">{event.address}</p>
                {event.description && <p className="mt-2 text-muted-foreground">{event.description}</p>}
              </div>
              <Button type="button" className="h-24 text-xl" disabled={attendanceMutation.isPending} onClick={() => handleAttendanceChoice("coming")}>
                מגיע
              </Button>
              <Button type="button" variant="outline" className="h-24 text-xl" disabled={attendanceMutation.isPending} onClick={() => handleAttendanceChoice("not_coming")}>
                לא מגיע
              </Button>
            </div>
          )}

          {step === "arrival" && (
            <div className="grid gap-4">
              <div className="rounded-lg border bg-muted/30 p-4 text-sm">
                <p className="font-medium">{event.name}</p>
                <p className="text-muted-foreground">{event.address}</p>
                {event.description && <p className="mt-2 text-muted-foreground">{event.description}</p>}
              </div>
              <Button type="button" className="h-24 text-xl" disabled={attendanceMutation.isPending} onClick={() => handleAttendanceChoice("arrived")}>
                הגעתי לאירוע
              </Button>
            </div>
          )}

          {step === "thank_you" && (
            <div className="rounded-lg border bg-muted/30 p-6 text-center">
              <p className="text-lg font-medium">תודה על העדכון</p>
              <p className="mt-2 text-sm text-muted-foreground">נעדכן את מנהל/ת האירוע שאינך מגיע/ה.</p>
            </div>
          )}

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
