import { useState } from "react"
import { useNavigate, Link } from "react-router-dom"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { login, setAccessToken } from "@/lib/api"

const schema = z.object({
  email: z.string().min(1, "נא להזין אימייל").email("אימייל לא תקין"),
  password: z.string().min(1, "נא להזין סיסמה"),
})

type FormData = z.infer<typeof schema>

export function LoginPage() {
  const navigate = useNavigate()
  const [error, setError] = useState<string | null>(null)
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
  })

  async function onSubmit(data: FormData) {
    setError(null)
    try {
      const res = await login(data.email, data.password)
      setAccessToken(res.access_token)
      navigate("/admin", { replace: true })
    } catch (e) {
      setError(e instanceof Error ? e.message : "התחברות נכשלה")
    }
  }

  return (
    <div className="container mx-auto flex min-h-screen items-center justify-center p-6" dir="rtl">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle>התחברות למנהלי חמ״ל</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="grid gap-4">
            <div className="grid gap-2">
              <Label htmlFor="email">אימייל</Label>
              <Input
                id="email"
                type="email"
                autoComplete="email"
                {...register("email")}
              />
              {errors.email && (
                <p className="text-sm text-destructive">{errors.email.message}</p>
              )}
            </div>
            <div className="grid gap-2">
              <Label htmlFor="password">סיסמה</Label>
              <Input
                id="password"
                type="password"
                autoComplete="current-password"
                {...register("password")}
              />
              {errors.password && (
                <p className="text-sm text-destructive">{errors.password.message}</p>
              )}
            </div>
            {error && <p className="text-sm text-destructive">{error}</p>}
            <Button type="submit" className="w-full" disabled={isSubmitting}>
              {isSubmitting ? "מתחבר..." : "התחבר"}
            </Button>
            <p className="text-center text-sm">
              <Link to="/forgot-password" className="underline">שכחתי סיסמה</Link>
            </p>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
