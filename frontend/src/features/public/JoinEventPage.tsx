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
}

interface JoinResponse {
  magic_token?: string
  need_details?: boolean
}

export function JoinEventPage() {
  const { eventId } = useParams<{ eventId: string }>()
  const navigate = useNavigate()
  const id = eventId ? parseInt(eventId, 10) : NaN
  const [needDetails, setNeedDetails] = useState(false)
  const [phoneValue, setPhoneValue] = useState("")

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
        navigate(`/event/${data.magic_token}`, { replace: true })
      } else if (data.need_details) {
        setNeedDetails(true)
      }
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
    formState: { errors: detailsErrors, isSubmitting: detailsSubmitting },
  } = useForm<DetailsForm>({
    resolver: zodResolver(detailsSchema),
  })

  useEffect(() => {
    if (needDetails && phoneValue) {
      setDetailsValue("phone", phoneValue)
    }
  }, [needDetails, phoneValue, setDetailsValue])

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
            הזן את מספר הטלפון שלך.
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          {!needDetails ? (
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
          ) : (
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
              <Button type="submit" className="w-full" disabled={detailsSubmitting}>
                {detailsSubmitting ? "שולח..." : "הצטרף לאירוע"}
              </Button>
              {joinMutation.isError && (
                <p className="text-sm text-destructive">
                  {joinMutation.error instanceof Error ? joinMutation.error.message : "שגיאה"}
                </p>
              )}
            </form>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
