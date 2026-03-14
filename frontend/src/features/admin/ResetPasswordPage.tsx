import { useState } from "react"
import { useSearchParams, Link } from "react-router-dom"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { apiRequest } from "@/lib/api"

const schema = z
  .object({
    new_password: z.string().min(6, "לפחות 6 תווים"),
    confirm: z.string(),
  })
  .refine((d) => d.new_password === d.confirm, { message: "הסיסמאות לא תואמות", path: ["confirm"] })

type FormData = z.infer<typeof schema>

export function ResetPasswordPage() {
  const [searchParams] = useSearchParams()
  const token = searchParams.get("token") ?? ""
  const [success, setSuccess] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const {
    register,
    handleSubmit,
    formState: { isSubmitting },
  } = useForm<FormData>({ resolver: zodResolver(schema) })

  async function onSubmit(data: FormData) {
    setError(null)
    try {
      await apiRequest("/api/v1/auth/reset-password", {
        method: "POST",
        body: JSON.stringify({ token, new_password: data.new_password }),
      })
      setSuccess(true)
    } catch (e) {
      setError(e instanceof Error ? e.message : "שגיאה")
    }
  }

  if (!token) {
    return (
      <div className="container mx-auto flex min-h-screen items-center justify-center p-6" dir="rtl">
        <Card className="w-full max-w-sm">
          <CardContent className="pt-6">
            <p className="text-center text-destructive">חסר קישור לאיפוס. נסה שוב מהאימייל.</p>
            <p className="mt-4 text-center">
              <Link to="/login" className="underline">להתחברות</Link>
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="container mx-auto flex min-h-screen items-center justify-center p-6" dir="rtl">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle>איפוס סיסמה</CardTitle>
        </CardHeader>
        <CardContent>
          {success ? (
            <p className="text-center">
              הסיסמה עודכנה. <Link to="/login" className="underline">התחבר</Link>
            </p>
          ) : (
            <form onSubmit={handleSubmit(onSubmit)} className="grid gap-4">
              <div className="grid gap-2">
                <Label htmlFor="new_password">סיסמה חדשה</Label>
                <Input id="new_password" type="password" {...register("new_password")} />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="confirm">אימות סיסמה</Label>
                <Input id="confirm" type="password" {...register("confirm")} />
              </div>
              {error && <p className="text-sm text-destructive">{error}</p>}
              <Button type="submit" className="w-full" disabled={isSubmitting}>
                {isSubmitting ? "מעדכן..." : "עדכן סיסמה"}
              </Button>
            </form>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
