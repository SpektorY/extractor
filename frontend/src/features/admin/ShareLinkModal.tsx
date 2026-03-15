import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"

interface ShareLinkModalProps {
  joinUrl: string
  onClose: () => void
  /** Optional: after create, show "Continue to control room" */
  onContinue?: () => void
}

export function ShareLinkModal({ joinUrl, onClose, onContinue }: ShareLinkModalProps) {
  const [copied, setCopied] = useState(false)

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(joinUrl)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // fallback: select and hope
      const input = document.createElement("input")
      input.value = joinUrl
      document.body.appendChild(input)
      input.select()
      document.execCommand("copy")
      document.body.removeChild(input)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      dir="rtl"
      onClick={onClose}
      onKeyDown={(e) => e.key === "Escape" && onClose()}
      role="dialog"
      aria-modal="true"
    >
      <Card
        className="mx-4 w-full max-w-lg"
        onClick={(e) => e.stopPropagation()}
      >
        <CardHeader className="flex-shrink-0">
          <CardTitle>קישור להזמנת מתנדבים</CardTitle>
          <p className="text-sm text-muted-foreground">
            שתף קישור זה עם מתנדבים. בלחיצה עליו יוזן מספר הטלפון ויופיעו באירוע.
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <Input readOnly value={joinUrl} className="font-mono text-sm" />
            <Button variant="outline" onClick={handleCopy}>
              {copied ? "הועתק!" : "העתק"}
            </Button>
          </div>
          <div className="flex gap-2 flex-wrap">
            {onContinue && (
              <Button onClick={onContinue}>
                המשך לדשבורד האירוע
              </Button>
            )}
            <Button variant="outline" onClick={onClose}>
              סגור
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
