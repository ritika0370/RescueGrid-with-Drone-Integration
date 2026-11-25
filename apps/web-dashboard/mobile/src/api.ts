import * as SecureStore from "expo-secure-store"

const API_URL = (process.env.EXPO_PUBLIC_API_BASE_URL || "http://localhost:8000").replace(/\/$/, "")
const DEMO_MODE = process.env.EXPO_PUBLIC_DEMO_MODE !== "false"

export type CitizenReportSummary = { id: string; category: string; status: string; submittedAt: string; address?: string }
export type CitizenReportDetail = CitizenReportSummary & {
  description?: string
  location?: { latitude: number; longitude: number; accuracyMeters?: number; source: "gps" | "manual" }
  media: Array<{ name: string; type: string; uri?: string }>
}

const demoReports: CitizenReportDetail[] = [
  { id: "DEMO-RPT-1042", category: "Fire", status: "Incident confirmed", submittedAt: "2026-11-24T09:42:00.000Z", address: "West Channel block · simulated", description: "Smoke reported near the west service entrance.", media: [] },
  { id: "DEMO-RPT-1008", category: "Flood", status: "Under review", submittedAt: "2026-11-24T08:16:00.000Z", address: "Riverside access · simulated", description: "Water is covering the lower access road.", media: [] },
]
const demoUpdates: Record<string, Array<{ at: string; text: string }>> = {}

export type ReportDraft = {
  category: string
  description: string
  location: { latitude: number; longitude: number; accuracyMeters?: number; source: "gps" | "manual" }
  address?: string
  peopleAffected?: number
  peopleTrapped?: number
  personallyInDanger?: boolean
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = await SecureStore.getItemAsync("cirrus-access-token")
  const headers = new Headers(init.headers)
  if (!(init.body instanceof FormData)) headers.set("Content-Type", "application/json")
  if (token) headers.set("Authorization", `Bearer ${token}`)
  const response = await fetch(`${API_URL}${path}`, { ...init, headers, credentials: "include" })
  if (!response.ok) throw new Error((await response.text()) || `Request failed (${response.status})`)
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export async function authenticate(mode: "login" | "register", credentials: { email: string; password: string }) {
  const endpoint = mode === "register" ? "/api/v1/auth/register" : "/api/v1/auth/login"
  const result = await request<{ accessToken?: string; access_token?: string; user?: { name: string; role: string } }>(endpoint, { method: "POST", body: JSON.stringify(credentials) })
  const token = result.accessToken || result.access_token
  if (token) await saveAccessToken(token)
  return result
}

export async function createReport(draft: ReportDraft) {
  if (DEMO_MODE) {
    const created: CitizenReportDetail = { id: `DEMO-RPT-${Math.random().toString(36).slice(2, 8).toUpperCase()}`, category: draft.category, status: "Submitted", submittedAt: new Date().toISOString(), address: draft.address || "Location details withheld", description: draft.description, location: draft.location, media: [] }
    demoReports.unshift(created)
    return created
  }
  const body = {
    emergency_category: draft.category,
    description: draft.description,
    latitude: draft.location?.latitude,
    longitude: draft.location?.longitude,
    location_accuracy: draft.location?.accuracyMeters,
    address_or_landmark: draft.address,
    people_affected: draft.peopleAffected ?? 0,
    people_trapped: draft.peopleTrapped ?? 0,
    reporter_safety_status: draft.personallyInDanger === true ? "AT_RISK" : draft.personallyInDanger === false ? "SAFE" : "UNKNOWN",
    submission_source: "APP",
  }
  const res = await request<{ report_id: string; initial_status: string; submission_timestamp: string; incident_id?: string }>("/api/v1/reports", { method: "POST", body: JSON.stringify(body) })
  return { id: res.report_id, category: draft.category, status: res.initial_status || "Submitted", submittedAt: res.submission_timestamp, address: draft.address, description: draft.description, location: draft.location, media: [] } as CitizenReportDetail
}

export async function getMyReports(): Promise<CitizenReportSummary[]> {
  if (DEMO_MODE) return demoReports.map(({ id, category, status, submittedAt, address }) => ({ id, category, status, submittedAt, address }))
  return request<CitizenReportSummary[]>("/api/v1/reports/my")
}

export async function getReportDetails(reportId: string): Promise<CitizenReportDetail> {
  if (DEMO_MODE) {
    const report = demoReports.find((item) => item.id === reportId)
    if (!report) throw new Error("Report not found in this demo session")
    return { ...report, media: [...report.media] }
  }
  return request<CitizenReportDetail>(`/api/v1/reports/${encodeURIComponent(reportId)}`)
}

export async function getReportStatus(reportId: string) {
  if (DEMO_MODE) return { status: demoReports.find((item) => item.id === reportId)?.status ?? "Submitted", updates: demoUpdates[reportId] ?? [] }
  return request<{ status: string; updates?: Array<{ at: string; text: string }> }>(`/api/v1/reports/${encodeURIComponent(reportId)}/status`)
}

export async function uploadReportMedia(reportId: string, file: { uri: string; name: string; type: string }) {
  if (DEMO_MODE) {
    const report = demoReports.find((item) => item.id === reportId)
    report?.media.push({ name: file.name, type: file.type, uri: file.uri })
    return { simulated: true }
  }
  const form = new FormData()
  form.append("file", { uri: file.uri, name: file.name, type: file.type } as unknown as Blob)
  return request(`/api/v1/reports/${encodeURIComponent(reportId)}/media`, { method: "POST", body: form })
}

export async function addReportUpdate(reportId: string, text: string) {
  if (DEMO_MODE) {
    const update = { at: new Date().toISOString(), text }
    demoUpdates[reportId] = [...(demoUpdates[reportId] ?? []), update]
    return { simulated: true, reportId, ...update }
  }
  return request(`/api/v1/reports/${encodeURIComponent(reportId)}/updates`, { method: "POST", body: JSON.stringify({ text }) })
}

export async function saveAccessToken(token: string) {
  await SecureStore.setItemAsync("cirrus-access-token", token)
}
