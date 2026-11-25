import type { Metadata } from "next"
import { CitizenApp } from "@/components/citizen/citizen-app"

export const dynamic = "force-dynamic"

export const metadata: Metadata = {
  title: "Emergency reporting by call or SOS | CIRRUS",
  description: "Share an emergency location with a fast SOS report or call the response desk when its phone line is configured.",
}

export default function CitizenPage() {
  const phone = process.env.TWILIO_PHONE_NUMBER?.trim()
  const dispatchPhone = process.env.TWILIO_DISPATCH_PHONE_NUMBER?.trim()
  const voiceReportingReady = Boolean(
    process.env.TWILIO_AUTH_TOKEN &&
      phone && /^\+[1-9]\d{7,14}$/.test(phone) &&
      dispatchPhone && /^\+[1-9]\d{7,14}$/.test(dispatchPhone),
  )

  return <CitizenApp emergencyPhone={voiceReportingReady ? phone : undefined} />
}
