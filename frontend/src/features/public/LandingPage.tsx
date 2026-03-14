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
  first_name: z.string().min(1, "נא להזין שם פרטי"),
  last_name: z.string().optional(),
  phone: z.string().min(1, "נא להזין טלפון"),
  area: z.string().optional(),
  group_tag: z.string().optional(),
})

type FormData = z.infer<typeof schema>

export function LandingPage() {
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
      await apiRequest("/api/v1/public/volunteer-signup", {
        method: "POST",
        body: JSON.stringify(data),
      })
      setSuccess(true)
    } catch (e) {
      setError(e instanceof Error ? e.message : "ההרשמה נכשלה")
    }
  }

  return (
    <div className="min-h-screen bg-muted/30 flex flex-col" dir="rtl">
      <div className="container mx-auto max-w-4xl p-6 flex-1 flex flex-col">
        <header className="py-6 text-center border-b border-border/50">
          <h1 className="text-4xl font-bold tracking-tight">המחלץ</h1>
          <p className="mt-6 text-xl text-muted-foreground max-w-2xl mx-auto leading-relaxed">
            כשמערכות התקשורת קורסות, הקשר האנושי הוא מציל חיים. <br />
            הצטרפו לרשת המתנדבים שמוודאת שאף תושב לא נשאר לבד ברגע האמת.
          </p>
        </header>
        <section className="mx-auto max-w-md py-6 flex-1">
          <Card className="shadow-sm">
            <CardHeader className="space-y-1.5">
              <CardTitle>הצטרף כמתנדב</CardTitle>
              <p className="text-sm text-muted-foreground">
                השאירו פרטים וניצור איתכם קשר.
              </p>
            </CardHeader>
            <CardContent>
              {success ? (
                <div className="rounded-lg border border-green-200 bg-green-50 dark:border-green-900/50 dark:bg-green-950/30 p-6 text-center">
                  <p className="text-green-700 dark:text-green-400 font-medium">
                    תודה! הפרטים נשלחו.
                  </p>
                  <p className="mt-1 text-sm text-muted-foreground">
                    ניצור איתכם קשר בהקדם.
                  </p>
                </div>
              ) : (
                <form onSubmit={handleSubmit(onSubmit)} className="grid gap-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="grid gap-2">
                      <Label htmlFor="first_name">שם פרטי</Label>
                      <Input id="first_name" autoComplete="given-name" {...register("first_name")} />
                    </div>
                    <div className="grid gap-2">
                      <Label htmlFor="last_name">שם משפחה</Label>
                      <Input id="last_name" autoComplete="family-name" {...register("last_name")} />
                    </div>
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="phone">טלפון</Label>
                    <Input id="phone" type="tel" autoComplete="tel" {...register("phone")} />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="area">אזור מגורים</Label>
                    <Input id="area" {...register("area")} placeholder="אופציונלי" />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="group_tag">קבוצה / התמחות</Label>
                    <Input id="group_tag" {...register("group_tag")} placeholder="למשל רפואה, סיירת שכונתית" />
                  </div>
                  {error && (
                    <div className="rounded-md border border-destructive/50 bg-destructive/10 px-3 py-2 text-sm text-destructive">
                      {error}
                    </div>
                  )}
                  <Button type="submit" className="w-full" disabled={isSubmitting}>
                    {isSubmitting ? "שולח..." : "שלח"}
                  </Button>
                </form>
              )}
            </CardContent>
          </Card>
        </section>

        <footer className="pt-8 pb-6 mt-auto border-t border-border/50 text-center text-sm text-muted-foreground">
          <Link to="/login" className="underline hover:text-foreground transition-colors">
            התחברות למנהלי חמ״ל
          </Link>
        </footer>
      </div>
    </div>
  )
}
