import { useState } from "react"
import { Link } from "react-router-dom"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { apiRequest } from "@/lib/api"

const schema = z.object({
  email: z.string().min(1, "נא להזין אימייל").email("אימייל לא תקין"),
})

type FormData = z.infer<typeof schema>

export function ForgotPasswordPage() {
  const [sent, setSent] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const {
    register,
    handleSubmit,
    formState: { isSubmitting },
  } = useForm<FormData>({ resolver: zodResolver(schema) })

  const [resetLink, setResetLink] = useState<string | null>(null)

  async function onSubmit(data: FormData) {
    setError(null)
    setResetLink(null)
    try {
      const res = await apiRequest<{ message?: string; reset_link?: string }>(
        "/api/v1/auth/forgot-password",
        {
          method: "POST",
          body: JSON.stringify({ email: data.email }),
        }
      )
      setSent(true)
      if (res?.reset_link) setResetLink(res.reset_link)
    } catch (e) {
      setError(e instanceof Error ? e.message : "שגיאה")
    }
  }

  return (
    <div className="container mx-auto flex min-h-screen items-center justify-center p-6" dir="rtl">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle>שכחתי סיסמה</CardTitle>
          <p className="text-sm text-muted-foreground">
            הזן את כתובת האימייל ונשלח אליך קישור לאיפוס. במצב פיתוח (כשהשרת מוגדר כך) יוצג גם קישור ישיר למטה.
          </p>
        </CardHeader>
        <CardContent>
          {sent ? (
            <div className="space-y-2 text-center text-muted-foreground">
              <p>אם החשבון קיים, נשלח אליך אימייל עם קישור לאיפוס. בדוק גם בתיקיית דואר זבל.</p>
            </div>
          ) : (
            <form onSubmit={handleSubmit(onSubmit)} className="grid gap-4">
              <div className="grid gap-2">
                <Label htmlFor="email">אימייל</Label>
                <Input id="email" type="email" {...register("email")} />
              </div>
              {error && <p className="text-sm text-destructive">{error}</p>}
              <Button type="submit" className="w-full" disabled={isSubmitting}>
                {isSubmitting ? "שולח..." : "שלח קישור"}
              </Button>
            </form>
          )}
          <p className="mt-4 text-center text-sm">
            <Link to="/login" className="underline">
              חזרה להתחברות
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
