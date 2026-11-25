/**
 * Centralized API client for RescueGrid AI / Disaster Response Platform.
 * Maps frontend domain types <-> backend API contracts (/api/v1).
 */
import type { CitizenReport, DashboardData, Incident, Mission, RealtimeEvent } from "@/shared/types"

const API_BASE_URL = (process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000").replace(/\/$/, "")

let authToken: string | null = null

export function setAuthToken(token: string | null) {
  authToken = token
  if (typeof window !== "undefined") {
    if (token) localStorage.setItem("rescuegrid_token", token)
    else localStorage.removeItem("rescuegrid_token")
  }
}

export function getAuthToken(): string | null {
  if (authToken) return authToken
  if (typeof window !== "undefined") {
    authToken = localStorage.getItem("rescuegrid_token")
  }
  return authToken
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers)
  if (!(init.body instanceof FormData)) {
    headers.set("Content-Type", "application/json")
  }
  const token = getAuthToken()
  if (token) headers.set("Authorization", `Bearer ${token}`)

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers,
    credentials: "include",
  })

  if (!response.ok) {
    let message = `Request failed (${response.status})`
    try {
      const body = await response.json()
      message = body.detail
        ? typeof body.detail === "string"
          ? body.detail
          : JSON.stringify(body.detail)
        : message
    } catch {
      const text = await response.text().catch(() => "")
      if (text) message = text
    }
    throw new ApiError(message, response.status)
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export class ApiError extends Error {
  constructor(message: string, public readonly status: number) {
    super(message)
    this.name = "ApiError"
  }
}

function mapReportToBackend(payload: Partial<CitizenReport> & Record<string, unknown>) {
  const loc = payload.location as { latitude?: number; longitude?: number; accuracyMeters?: number } | undefined
  return {
    emergency_category: payload.category ?? payload.emergency_category,
    description: payload.description ?? "",
    latitude: loc?.latitude ?? payload.latitude,
    longitude: loc?.longitude ?? payload.longitude,
    location_accuracy: loc?.accuracyMeters,
    address_or_landmark: payload.address ?? payload.address_or_landmark,
    people_affected: payload.peopleAffected ?? payload.people_affected ?? 0,
    people_trapped: payload.peopleTrapped ?? payload.people_trapped ?? 0,
    reporter_safety_status:
      payload.personallyInDanger === true
        ? "AT_RISK"
        : payload.personallyInDanger === false
          ? "SAFE"
          : payload.reporter_safety_status ?? "UNKNOWN",
    reporter_name: payload.reporter_name ?? payload.reporterName,
    reporter_phone: payload.reporter_phone ?? payload.reporterPhone,
    submission_source: "APP",
  }
}

function mapReportFromBackend(r: any): CitizenReport {
  return {
    id: r.id ?? r.report_id,
    incidentId: r.incident_id ?? r.incidentId,
    category: r.emergency_category ?? r.category,
    description: r.description ?? "",
    submittedAt: r.created_at ?? r.submission_timestamp ?? r.submittedAt ?? new Date().toISOString(),
    location: {
      latitude: r.latitude ?? 0,
      longitude: r.longitude ?? 0,
      accuracyMeters: r.location_accuracy,
      source: r.manually_entered_location ? "manual" : "gps",
    },
    address: r.address_or_landmark ?? r.address ?? "",
    status: mapReportStatus(r.status ?? r.initial_status ?? "Submitted"),
    peopleAffected: r.people_affected,
    peopleTrapped: r.people_trapped,
    personallyInDanger: r.reporter_safety_status === "AT_RISK" || r.reporter_safety_status === "TRAPPED",
    media: (r.media ?? []).map((m: any) => ({
      id: m.id,
      type: (m.media_type ?? m.type ?? "image").toLowerCase().includes("audio")
        ? "audio"
        : (m.media_type ?? m.type ?? "image").toLowerCase().includes("video")
          ? "video"
          : "image",
      url: m.storage_path ? `${API_BASE_URL}/uploads/${m.storage_path.replace(/^uploads\//, "")}` : m.url ?? "",
      label: m.original_filename ?? m.label ?? "media",
    })),
  }
}

function mapReportStatus(s: string): CitizenReport["status"] {
  const map: Record<string, CitizenReport["status"]> = {
    SUBMITTED: "Submitted",
    UNDER_REVIEW: "Under review",
    GROUPED: "Incident confirmed",
    ASSIGNED: "Assigned to department",
    MISSION_ASSIGNED: "Drone survey assigned",
    IN_PROGRESS: "Survey in progress",
    RESOLVED: "Resolved",
    CLOSED: "Closed",
  }
  return map[s] ?? (s as CitizenReport["status"]) ?? "Submitted"
}

function mapIncidentFromBackend(i: any): Incident {
  return {
    id: i.id ?? i.incident_id,
    category: i.primary_category ?? i.category ?? "Other emergency",
    priority: mapPriority(i.priority ?? i.suggested_priority ?? "P3"),
    status: mapIncidentStatus(i.status),
    title: i.title ?? i.summary?.slice(0, 80) ?? "Incident",
    area: i.area_description ?? i.area ?? "",
    location: {
      latitude: i.centroid_latitude ?? i.latitude ?? 0,
      longitude: i.centroid_longitude ?? i.longitude ?? 0,
      source: "gps",
    },
    firstReportedAt: i.created_at ?? i.first_reported_at ?? new Date().toISOString(),
    updatedAt: i.updated_at ?? i.created_at ?? new Date().toISOString(),
    department: i.assigned_department_name ?? i.department ?? "Unassigned",
    departmentId: i.assigned_department_id ?? i.department_id,
    linkedReports: (i.reports ?? i.linked_reports ?? []).map(mapReportFromBackend),
    peopleAffected: i.total_people_affected ?? i.people_affected,
    peopleTrapped: i.total_people_trapped ?? i.people_trapped,
    summary: i.ai_summary ?? i.summary ?? "",
    confidence: i.grouping_confidence ?? i.confidence ?? 0.5,
    hazards: i.hazards ?? [],
    notes: i.notes ?? [],
  }
}

function mapPriority(p: string): Incident["priority"] {
  const map: Record<string, Incident["priority"]> = {
    P1: "Critical", P2: "High", P3: "Medium", P4: "Low",
    Critical: "Critical", High: "High", Medium: "Medium", Low: "Low",
  }
  return map[p] ?? "Medium"
}

function mapIncidentStatus(s: string): Incident["status"] {
  const map: Record<string, Incident["status"]> = {
    PROVISIONAL: "Under review", CONFIRMED: "Confirmed", ASSIGNED: "Assigned",
    SURVEY_IN_PROGRESS: "Survey in progress", RESCUE_NOTIFIED: "Rescue team notified",
    RESOLVED: "Resolved", CLOSED: "Closed",
  }
  return map[s] ?? (s as Incident["status"]) ?? "Under review"
}

function mapMissionFromBackend(m: any): Mission {
  return {
    id: m.id ?? m.mission_id,
    incidentId: m.incident_id,
    category: m.incident_category ?? m.category ?? "Other emergency",
    priority: mapPriority(m.priority ?? "P3"),
    objective: m.objective ?? m.mission_objective ?? "",
    area: m.survey_area_description ?? m.area ?? "",
    boundary: (m.survey_boundary ?? m.boundary ?? []).map((c: any) => ({
      latitude: c.lat ?? c.latitude,
      longitude: c.lng ?? c.longitude,
      source: "gps" as const,
    })),
    hazards: m.known_hazards ?? m.hazards ?? [],
    instructions: m.special_instructions ?? m.instructions ?? "",
    requiredObservations: m.survey_requirements ?? m.required_observations ?? [],
    droneId: m.assigned_drone_id ?? m.drone_id ?? "",
    pilot: m.assigned_pilot_name ?? m.pilot ?? "",
    createdAt: m.created_at ?? new Date().toISOString(),
    status: mapMissionStatus(m.status),
    observations: (m.observations ?? []).map((o: any) => ({
      id: o.id,
      classification: o.classification ?? "Possible observation",
      kind: o.kind ?? o.observation_type ?? "",
      description: o.description ?? "",
      location: { latitude: o.latitude ?? 0, longitude: o.longitude ?? 0, source: "gps" as const },
      observedAt: o.created_at ?? o.observed_at ?? new Date().toISOString(),
      source: o.source ?? "pilot",
    })),
  }
}

function mapMissionStatus(s: string): Mission["status"] {
  const map: Record<string, Mission["status"]> = {
    DRAFT: "Awaiting pilot", APPROVED: "Awaiting pilot", ASSIGNED: "Awaiting pilot",
    ACCEPTED: "Accepted", IN_PROGRESS: "In flight", PAUSED: "Paused",
    COMPLETED: "Completed", CANCELLED: "Rejected", REJECTED: "Rejected",
  }
  return map[s] ?? (s as Mission["status"]) ?? "Awaiting pilot"
}

export const api = {
  login: async (credentials: { email: string; password: string }) => {
    const res = await request<{
      access_token: string; token_type: string; role: string; name: string; user_id: string; department_id?: string | null
    }>("/api/v1/auth/login", { method: "POST", body: JSON.stringify(credentials) })
    setAuthToken(res.access_token)
    return {
      accessToken: res.access_token,
      user: { name: res.name, role: res.role, id: res.user_id, departmentId: res.department_id },
    }
  },

  createReport: async (payload: Partial<CitizenReport> & Record<string, unknown>) => {
    const body = mapReportToBackend(payload)
    const res = await request<any>("/api/v1/reports", { method: "POST", body: JSON.stringify(body) })
    return {
      id: res.report_id,
      status: mapReportStatus(res.initial_status ?? "SUBMITTED"),
      submittedAt: res.submission_timestamp,
      incidentId: res.incident_id,
      category: payload.category as CitizenReport["category"],
      description: payload.description ?? "",
      location: payload.location ?? { latitude: 0, longitude: 0, source: "gps" },
      address: payload.address ?? "",
      media: [],
    } as CitizenReport
  },

  myReports: async () => {
    const list = await request<any[]>("/api/v1/reports/my")
    return list.map(mapReportFromBackend)
  },

  report: async (id: string) => mapReportFromBackend(await request<any>(`/api/v1/reports/${encodeURIComponent(id)}`)),

  reportStatus: (id: string) =>
    request<{ status: string; updates?: Array<{ at: string; text: string }> }>(`/api/v1/reports/${encodeURIComponent(id)}/status`),

  addReportUpdate: (id: string, payload: { text?: string }) =>
    request(`/api/v1/reports/${encodeURIComponent(id)}/updates`, { method: "POST", body: JSON.stringify(payload) }),

  uploadReportMedia: (id: string, formData: FormData) =>
    request(`/api/v1/reports/${encodeURIComponent(id)}/media`, { method: "POST", body: formData }),

  incidents: async () => (await request<any[]>("/api/v1/incidents")).map(mapIncidentFromBackend),

  incident: async (id: string) => mapIncidentFromBackend(await request<any>(`/api/v1/incidents/${encodeURIComponent(id)}`)),

  updateIncident: async (id: string, patch: Partial<Incident> & Record<string, unknown>) => {
    const body: Record<string, unknown> = {}
    if (patch.priority) {
      const pmap: Record<string, string> = { Critical: "P1", High: "P2", Medium: "P3", Low: "P4" }
      body.priority = pmap[patch.priority] ?? patch.priority
    }
    if (patch.status) body.status = patch.status
    if (patch.notes) body.notes = patch.notes
    return mapIncidentFromBackend(await request<any>(`/api/v1/incidents/${encodeURIComponent(id)}`, {
      method: "PATCH", body: JSON.stringify(body),
    }))
  },

  assignIncident: (id: string, departmentId: string) =>
    request(`/api/v1/incidents/${encodeURIComponent(id)}/assign`, {
      method: "POST", body: JSON.stringify({ department_id: departmentId }),
    }),

  linkReport: (incidentId: string, reportId: string) =>
    request(`/api/v1/incidents/${encodeURIComponent(incidentId)}/reports/${encodeURIComponent(reportId)}`, { method: "POST" }),

  unlinkReport: (incidentId: string, reportId: string) =>
    request(`/api/v1/incidents/${encodeURIComponent(incidentId)}/reports/${encodeURIComponent(reportId)}`, { method: "DELETE" }),

  reviewGrouping: (incidentId: string, decision: "confirm" | "reject") =>
    request(`/api/v1/incidents/${encodeURIComponent(incidentId)}/grouping`, {
      method: "POST", body: JSON.stringify({ decision }),
    }),

  createJobCard: async (incidentId: string, payload: Partial<Mission> & Record<string, unknown>) => {
    const body = {
      incident_id: incidentId,
      objective: payload.objective ?? "Aerial survey of affected area",
      assigned_drone_id: payload.droneId ?? payload.assigned_drone_id,
      assigned_pilot_id: payload.pilotId ?? payload.assigned_pilot_id,
      special_instructions: payload.instructions ?? payload.special_instructions,
      survey_requirements: payload.requiredObservations ?? [],
    }
    return mapMissionFromBackend(await request<any>("/api/v1/missions", {
      method: "POST", body: JSON.stringify(body),
    }))
  },

  jobCards: async () => (await request<any[]>("/api/v1/missions")).map(mapMissionFromBackend),

  jobCard: async (id: string) => mapMissionFromBackend(await request<any>(`/api/v1/missions/${encodeURIComponent(id)}`)),

  acceptMission: (id: string) =>
    request(`/api/v1/missions/${encodeURIComponent(id)}/accept`, { method: "POST", body: JSON.stringify({}) }),

  updateMissionStatus: (id: string, status: string, reason?: string) =>
    request(`/api/v1/missions/${encodeURIComponent(id)}/status`, {
      method: "POST", body: JSON.stringify({ status, reason }),
    }),

  submitFindings: (id: string, payload: Record<string, unknown>) =>
    request(`/api/v1/missions/${encodeURIComponent(id)}/observations`, {
      method: "POST", body: JSON.stringify(payload),
    }),

  drones: async () => {
    const list = await request<any[]>("/api/v1/drones")
    return list.map((d: any) => ({
      id: d.id,
      model: d.name ?? d.model ?? "Drone",
      station: d.station_name ?? d.station ?? "",
      location: {
        latitude: d.last_latitude ?? d.latitude ?? 0,
        longitude: d.last_longitude ?? d.longitude ?? 0,
        source: "gps" as const,
      },
      batteryPercent: d.battery_percentage ?? d.battery_percent,
      status: (d.availability_status ?? d.status ?? "Available") as any,
      missionId: d.current_mission_id,
      lastCommunicationAt: d.last_telemetry_at,
      simulated: d.is_simulated ?? true,
    }))
  },

  unlinkedReports: async () => {
    try {
      return (await request<any[]>("/api/v1/reports?unlinked=true")).map(mapReportFromBackend)
    } catch { return [] }
  },

  departments: async () => {
    const list = await request<any[]>("/api/v1/departments")
    return list.map((d: any) => ({
      id: d.id, name: d.name,
      location: { latitude: d.latitude ?? 0, longitude: d.longitude ?? 0, source: "gps" as const },
      simulated: true,
    }))
  },

  droneStations: async () => {
    const list = await request<any[]>("/api/v1/drones/stations")
    return list.map((s: any) => ({
      id: s.id, name: s.name,
      location: { latitude: s.latitude ?? 0, longitude: s.longitude ?? 0, source: "gps" as const },
      availableDrones: s.available_drones, simulated: true,
    }))
  },

  dashboard: async (): Promise<DashboardData> => {
    const [incidents, drones, missions, departments, droneStations] = await Promise.all([
      api.incidents().catch(() => []),
      api.drones().catch(() => []),
      api.jobCards().catch(() => []),
      api.departments().catch(() => []),
      api.droneStations().catch(() => []),
    ])
    return {
      incidents, drones, missions, departments, droneStations,
      unlinkedReports: [],
      recentActivity: incidents.slice(0, 5).map((i) => ({
        id: i.id, title: i.title, detail: `${i.priority} · ${i.status}`,
        at: i.updatedAt,
        tone: i.priority === "Critical" ? "red" : i.priority === "High" ? "orange" : "blue",
      })),
      simulated: false,
    }
  },
}

export function subscribeToEvents(
  onEvent: (event: RealtimeEvent) => void,
  onState?: (state: "connecting" | "connected" | "disconnected") => void
) {
  const configuredUrl = process.env.NEXT_PUBLIC_WS_URL || `${API_BASE_URL.replace(/^http/, "ws")}/api/v1/ws/events`
  if (process.env.NEXT_PUBLIC_DEMO_MODE === "true") {
    onState?.("disconnected")
    return () => undefined
  }
  try {
    const socket = new WebSocket(configuredUrl)
    onState?.("connecting")
    socket.addEventListener("open", () => onState?.("connected"))
    socket.addEventListener("close", () => onState?.("disconnected"))
    socket.addEventListener("error", () => onState?.("disconnected"))
    socket.addEventListener("message", (message) => {
      try { onEvent(JSON.parse(message.data) as RealtimeEvent) }
      catch { console.error("Received an unreadable realtime event") }
    })
    return () => socket.close()
  } catch {
    onState?.("disconnected")
    return () => undefined
  }
}

export function isDemoMode() {
  return process.env.NEXT_PUBLIC_DEMO_MODE === "true"
}
