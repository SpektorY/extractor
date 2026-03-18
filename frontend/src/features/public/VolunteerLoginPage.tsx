import { useState } from "react"
import { useLocation, useNavigate } from "react-router-dom"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { requestVolunteerOtp, setVolunteerAccessToken, verifyVolunteerOtp } from "@/lib/api"

type Step = "phone" | "otp"

export function VolunteerLoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const returnTo = (location.state as { returnTo?: string } | undefined)?.returnTo ?? "/"
  const [step, setStep] = useState<Step>("phone")
  const [phone, setPhone] = useState("")
  const [code, setCode] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function sendOtp() {
    setError(null)
    if (!phone.trim()) {
      setError("נא להזין טלפון")
      return
    }
    setLoading(true)
    try {
      await requestVolunteerOtp(phone.trim())
      setStep("otp")
    } catch (e) {
      setError(e instanceof Error ? e.message : "שגיאה בשליחת הקוד")
    } finally {
      setLoading(false)
    }
  }

  async function verifyOtp() {
    setError(null)
    if (!code.trim()) {
      setError("נא להזין קוד")
      return
    }
    setLoading(true)
    try {
      const res = await verifyVolunteerOtp(phone.trim(), code.trim())
      setVolunteerAccessToken(res.access_token)
      navigate(returnTo, { replace: true })
    } catch (e) {
      setError(e instanceof Error ? e.message : "אימות קוד נכשל")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container mx-auto flex min-h-screen items-center justify-center p-6" dir="rtl">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle>התחברות מתנדבים</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {step === "phone" && (
            <>
              <div className="grid gap-2">
                <Label htmlFor="phone">טלפון</Label>
                <Input
                  id="phone"
                  type="tel"
                  autoComplete="tel"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                />
              </div>
              <Button className="w-full" onClick={sendOtp} disabled={loading}>
                {loading ? "שולח..." : "שלח קוד"}
              </Button>
            </>
          )}
          {step === "otp" && (
            <>
              <p className="text-sm text-muted-foreground">שלחנו קוד לטלפון {phone}</p>
              <div className="grid gap-2">
                <Label htmlFor="code">קוד OTP</Label>
                <Input
                  id="code"
                  inputMode="numeric"
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                />
              </div>
              <Button className="w-full" onClick={verifyOtp} disabled={loading}>
                {loading ? "מאמת..." : "אימות והמשך"}
              </Button>
              <Button variant="outline" className="w-full" onClick={() => setStep("phone")} disabled={loading}>
                החלף טלפון
              </Button>
            </>
          )}
          {error && <p className="text-sm text-destructive">{error}</p>}
        </CardContent>
      </Card>
    </div>
  )
}
