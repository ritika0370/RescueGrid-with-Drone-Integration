import twilio from "twilio"

const E164_PHONE_PATTERN = /^\+[1-9]\d{7,14}$/

function xmlResponse(body: string, status = 200) {
  return new Response(body, {
    status,
    headers: {
      "Content-Type": "text/xml; charset=utf-8",
      "Cache-Control": "no-store",
    },
  })
}

export async function POST(request: Request) {
  const authToken = process.env.TWILIO_AUTH_TOKEN
  const incomingPhone = process.env.TWILIO_PHONE_NUMBER?.trim()
  const dispatchPhone = process.env.TWILIO_DISPATCH_PHONE_NUMBER?.trim()
  const signature = request.headers.get("x-twilio-signature")
  const contentType = request.headers.get("content-type") || ""

  if (
    !authToken ||
    !incomingPhone ||
    !E164_PHONE_PATTERN.test(incomingPhone) ||
    !dispatchPhone ||
    !E164_PHONE_PATTERN.test(dispatchPhone)
  ) {
    return new Response("Voice reporting is not configured.", { status: 503 })
  }

  if (!contentType.toLowerCase().startsWith("application/x-www-form-urlencoded")) {
    return new Response("Unsupported content type.", { status: 415 })
  }

  if (!signature) {
    return new Response("Forbidden.", { status: 403 })
  }

  let formData: FormData
  try {
    formData = await request.formData()
  } catch {
    return new Response("Invalid request body.", { status: 400 })
  }

  const parameters: Record<string, string> = {}
  for (const [key, value] of formData.entries()) {
    if (typeof value === "string") parameters[key] = value
  }

  const webhookUrl = process.env.TWILIO_VOICE_WEBHOOK_URL?.trim() || request.url
  const isTwilioRequest = twilio.validateRequest(authToken, signature, webhookUrl, parameters)

  if (!isTwilioRequest || parameters.To !== incomingPhone) {
    return new Response("Forbidden.", { status: 403 })
  }

  const voiceResponse = new twilio.twiml.VoiceResponse()
  voiceResponse.say(
    { voice: "alice" },
    "Thank you for calling the Cirrus response desk. Please stay on the line while we connect you.",
  )
  voiceResponse.dial({ timeout: 25, answerOnBridge: true }).number(dispatchPhone)
  voiceResponse.say(
    { voice: "alice" },
    "The response desk could not answer. If you are in immediate danger, contact your local emergency services now.",
  )
  voiceResponse.hangup()

  return xmlResponse(voiceResponse.toString())
}
