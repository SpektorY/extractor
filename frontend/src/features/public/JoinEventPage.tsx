import { useState, useEffect } from "react"
import { useParams, useNavigate } from "react-router-dom"
import { useQuery, useMutation } from "@tanstack/react-query"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { apiRequest } from "@/lib/api"

const phoneSchema = z.object({
  phone: z.string().min(1, "נא להזין טלפון"),
})

const detailsSchema = z.object({
  first_name: z.string().min(1, "נא להזין שם פרטי"),
  last_name: z.string().optional(),
  phone: z.string().min(1, "נא להזין טלפון"),
  area: z.string().optional(),
  group_tag: z.string().optional(),
})

type PhoneForm = z.infer<typeof phoneSchema>
type DetailsForm = z.infer<typeof detailsSchema>

interface EventPublic {
  id: number
  name: string
  address: string
  description?: string | null
}

type AttendanceStatus = "coming" | "not_coming" | "arrived" | "left"

interface JoinResponse {
  magic_token?: string
  need_details?: boolean
  attendance_status?: AttendanceStatus | null
}

export function JoinEventPage() {
  const { eventId } = useParams<{ eventId: string }>()
  const navigate = useNavigate()
  const id = eventId ? parseInt(eventId, 10) : NaN
  const [step, setStep] = useState<"phone" | "details" | "response" | "arrival" | "thank_you">("phone")
  const [phoneValue, setPhoneValue] = useState("")
  const [eventToken, setEventToken] = useState<string | null>(null)

  const { data: event, isLoading: loadingEvent, error: eventError } = useQuery({
    queryKey: ["public-event", id],
    queryFn: () => apiRequest<EventPublic>(`/api/v1/public/event/${id}`),
    enabled: Number.isInteger(id),
  })

  const joinMutation = useMutation({
    mutationFn: async (body: { phone: string; first_name?: string; last_name?: string; area?: string; group_tag?: string }) => {
      const res = await fetch(
        `${import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"}/api/v1/public/event/${id}/join`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        }
      )
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(typeof err.detail === "string" ? err.detail : "שגיאה")
      }
      return res.json() as Promise<JoinResponse>
    },
    onSuccess: (data) => {
      if (data.magic_token) {
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
      } else if (data.need_details) {
        setStep("details")
      }
    },
  })

  const attendanceMutation = useMutation({
    mutationFn: async (status: AttendanceStatus) => {
      if (!eventToken) throw new Error("קישור האירוע לא זמין")
      const res = await fetch(
        `${import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"}/api/v1/event-by-token/${eventToken}/attendance`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ status }),
        }
      )
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(typeof err.detail === "string" ? err.detail : "שגיאה")
      }
      return res.json() as Promise<{ status: AttendanceStatus }>
    },
  })

  const {
    register: registerPhone,
    handleSubmit: handlePhoneSubmit,
    formState: { errors: phoneErrors },
  } = useForm<PhoneForm>({ resolver: zodResolver(phoneSchema) })

  const {
    register: registerDetails,
    handleSubmit: handleDetailsSubmit,
    setValue: setDetailsValue,
    formState: { errors: detailsErrors },
  } = useForm<DetailsForm>({
    resolver: zodResolver(detailsSchema),
  })

  useEffect(() => {
    if (step === "details" && phoneValue) {
      setDetailsValue("phone", phoneValue)
    }
  }, [step, phoneValue, setDetailsValue])

  function onPhoneSubmit(data: PhoneForm) {
    setPhoneValue(data.phone)
    joinMutation.mutate({ phone: data.phone })
  }

  function onDetailsSubmit(data: DetailsForm) {
    joinMutation.mutate({
      phone: data.phone,
      first_name: data.first_name,
      last_name: data.last_name,
      area: data.area,
      group_tag: data.group_tag,
    })
  }

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

  if (loadingEvent || eventError || !event) {
    return (
      <div className="flex min-h-screen items-center justify-center p-6" dir="rtl">
        {eventError ? (
          <Card className="w-full max-w-sm">
            <CardContent className="pt-6">
              <p className="text-center text-destructive">
                אירוע לא נמצא או שהקישור לא תקין.
              </p>
            </CardContent>
          </Card>
        ) : (
          <p className="text-muted-foreground">טוען...</p>
        )}
      </div>
    )
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-6" dir="rtl">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>הצטרפות לאירוע: {event.name}</CardTitle>
          <p className="text-sm text-muted-foreground">
            {step === "phone" && "הזן את מספר הטלפון שלך."}
            {step === "details" && "נראה שזו הפעם הראשונה שלך כאן. מלא/י כמה פרטים קצרים."}
            {step === "response" && "האם את/ה מגיע/ה לאירוע?"}
            {step === "arrival" && "כשתגיע/י לאירוע, אשר/י הגעה כדי להיכנס ללוח המתנדבים."}
            {step === "thank_you" && "תודה שעדכנת אותנו."}
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          {step === "phone" && (
            <form onSubmit={handlePhoneSubmit(onPhoneSubmit)} className="grid gap-4">
              <div className="grid gap-2">
                <Label htmlFor="phone">טלפון</Label>
                <Input
                  id="phone"
                  type="tel"
                  autoComplete="tel"
                  {...registerPhone("phone")}
                />
                {phoneErrors.phone && (
                  <p className="text-sm text-destructive">{phoneErrors.phone.message}</p>
                )}
              </div>
              <Button
                type="submit"
                className="w-full"
                disabled={joinMutation.isPending}
              >
                {joinMutation.isPending ? "בודק..." : "המשך"}
              </Button>
              {joinMutation.isError && (
                <p className="text-sm text-destructive">
                  {joinMutation.error instanceof Error ? joinMutation.error.message : "שגיאה"}
                </p>
              )}
            </form>
          )}

          {step === "details" && (
            <form onSubmit={handleDetailsSubmit(onDetailsSubmit)} className="grid gap-4">
              <input type="hidden" {...registerDetails("phone")} />
              <div className="grid grid-cols-2 gap-4">
                <div className="grid gap-2">
                  <Label htmlFor="first_name">שם פרטי</Label>
                  <Input id="first_name" autoComplete="given-name" {...registerDetails("first_name")} />
                  {detailsErrors.first_name && (
                    <p className="text-sm text-destructive">{detailsErrors.first_name.message}</p>
                  )}
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="last_name">שם משפחה</Label>
                  <Input id="last_name" autoComplete="family-name" {...registerDetails("last_name")} />
                </div>
              </div>
              <div className="grid gap-2">
                <Label htmlFor="area">אזור מגורים</Label>
                <Input id="area" {...registerDetails("area")} placeholder="אופציונלי" />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="group_tag">קבוצה / התמחות</Label>
                <Input id="group_tag" {...registerDetails("group_tag")} placeholder="אופציונלי" />
              </div>
              <Button type="submit" className="w-full" disabled={joinMutation.isPending}>
                {joinMutation.isPending ? "שולח..." : "הצטרף לאירוע"}
              </Button>
              {joinMutation.isError && (
                <p className="text-sm text-destructive">
                  {joinMutation.error instanceof Error ? joinMutation.error.message : "שגיאה"}
                </p>
              )}
            </form>
          )}

          {step === "response" && (
            <div className="grid gap-4">
              <div className="rounded-lg border bg-muted/30 p-4 text-sm">
                <p className="font-medium">{event.name}</p>
                <p className="text-muted-foreground">{event.address}</p>
                {event.description && (
                  <p className="mt-2 text-muted-foreground">{event.description}</p>
                )}
              </div>
              <Button
                type="button"
                className="h-24 text-xl"
                disabled={attendanceMutation.isPending}
                onClick={() => handleAttendanceChoice("coming")}
              >
                מגיע
              </Button>
              <Button
                type="button"
                variant="outline"
                className="h-24 text-xl"
                disabled={attendanceMutation.isPending}
                onClick={() => handleAttendanceChoice("not_coming")}
              >
                לא מגיע
              </Button>
              {attendanceMutation.isError && (
                <p className="text-sm text-destructive">
                  {attendanceMutation.error instanceof Error ? attendanceMutation.error.message : "שגיאה"}
                </p>
              )}
            </div>
          )}

          {step === "arrival" && (
            <div className="grid gap-4">
              <div className="rounded-lg border bg-muted/30 p-4 text-sm">
                <p className="font-medium">{event.name}</p>
                <p className="text-muted-foreground">{event.address}</p>
                {event.description && (
                  <p className="mt-2 text-muted-foreground">{event.description}</p>
                )}
              </div>
              <Button
                type="button"
                className="h-24 text-xl"
                disabled={attendanceMutation.isPending}
                onClick={() => handleAttendanceChoice("arrived")}
              >
                הגעתי לאירוע
              </Button>
              {attendanceMutation.isError && (
                <p className="text-sm text-destructive">
                  {attendanceMutation.error instanceof Error ? attendanceMutation.error.message : "שגיאה"}
                </p>
              )}
            </div>
          )}

          {step === "thank_you" && (
            <div className="rounded-lg border bg-muted/30 p-6 text-center">
              <p className="text-lg font-medium">תודה על העדכון</p>
              <p className="mt-2 text-sm text-muted-foreground">
                נעדכן את מנהל/ת האירוע שאינך מגיע/ה.
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
