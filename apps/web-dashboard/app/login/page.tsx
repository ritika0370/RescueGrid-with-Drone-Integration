"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { AlertTriangle, ArrowLeft, LockKeyhole, ShieldCheck } from "lucide-react"
import { api, isDemoMode } from "@/lib/api"
import { BRAND } from "@/shared/design-system"

const roles = ["Super Administrator", "Department Administrator", "Incident Officer", "Drone Pilot", "Read-only Viewer"]

export default function DepartmentLoginPage() {
  const router = useRouter()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [message, setMessage] = useState("")
  const [busy, setBusy] = useState(false)
  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setBusy(true)
    setMessage("")
    try {
      const response = await api.login({ email, password })
      setMessage(`Signed in as ${response.user.role}.`)
      router.push("/")
    } catch {
      setMessage("Authentication service unavailable. Connect the backend identity endpoint to sign in.")
    } finally { setBusy(false) }
  }
  return <main className="login-page"><a href="/" className="login-back"><ArrowLeft size={15} />Back to operations</a><section className="login-card"><div className="login-mark"><span>C</span></div><span className="login-prototype">PROTOTYPE · AUTHENTICATION REQUIRED</span><h1>Department sign in</h1><p>Access is granted by the connected identity service. Frontend role labels do not grant permissions.</p><form onSubmit={submit}><label htmlFor="login-email">Work email</label><input id="login-email" type="email" autoComplete="username" required value={email} onChange={(event) => setEmail(event.target.value)} placeholder="name@department.gov" /><label htmlFor="login-password">Password</label><input id="login-password" type="password" autoComplete="current-password" required value={password} onChange={(event) => setPassword(event.target.value)} placeholder="Enter password" /><button type="submit" disabled={busy}><LockKeyhole size={15} />{busy ? "Connecting…" : "Sign in"}</button>{message ? <div className="login-message" role="status"><AlertTriangle size={14} />{message}</div> : null}</form><div className="login-role-list"><div><ShieldCheck size={14} />Backend-managed roles</div><span>{roles.join(" · ")}</span></div><small className="login-no-demo">{isDemoMode() ? "Demo mode is read-only. No demo credentials are created." : "Role permissions are enforced by the backend."}</small></section><footer className="login-footer">CIRRUS · {BRAND.descriptor} · Prototype, no official agency affiliation</footer></main>
}
