export const EMERGENCY_CATEGORIES = [
  "Fire",
  "Flood",
  "Earthquake",
  "Building collapse",
  "Road accident",
  "Medical emergency",
  "Missing or trapped person",
  "Other emergency",
] as const

export type EmergencyCategory = (typeof EMERGENCY_CATEGORIES)[number]
export type Priority = "Critical" | "High" | "Medium" | "Low"
export type IncidentStatus =
  | "Under review"
  | "Confirmed"
  | "Assigned"
  | "Survey in progress"
  | "Rescue team notified"
  | "Resolved"
  | "Closed"
export type ReportStatus =
  | "Submitted"
  | "Under review"
  | "Incident confirmed"
  | "Assigned to department"
  | "Drone survey assigned"
  | "Survey in progress"
  | "Rescue team notified"
  | "Resolved"
  | "Closed"
export type DroneStatus =
  | "Available"
  | "Assigned"
  | "Preparing"
  | "In flight"
  | "Returning"
  | "Charging"
  | "Offline"
  | "Maintenance"

export interface Coordinates {
  latitude: number
  longitude: number
  accuracyMeters?: number
  source: "gps" | "manual" | "simulated"
}

export interface CitizenReport {
  id: string
  incidentId?: string
  category: EmergencyCategory
  description: string
  submittedAt: string
  location: Coordinates
  address: string
  status: ReportStatus
  peopleAffected?: number
  peopleTrapped?: number
  personallyInDanger?: boolean
  media: Array<{ id: string; type: "image" | "audio" | "video"; url: string; label: string }>
}

export interface Incident {
  id: string
  category: EmergencyCategory
  priority: Priority
  status: IncidentStatus
  title: string
  area: string
  location: Coordinates
  firstReportedAt: string
  updatedAt: string
  department: string
  departmentId?: string
  linkedReports: CitizenReport[]
  peopleAffected?: number
  peopleTrapped?: number
  summary: string
  confidence: number
  hazards: string[]
  notes: string[]
}

export interface ResponseDepartment {
  id: string
  name: string
  location: Coordinates
  simulated?: boolean
}

export interface DroneStation {
  id: string
  name: string
  location: Coordinates
  availableDrones?: number
  simulated?: boolean
}

export interface Drone {
  id: string
  model: string
  station: string
  location: Coordinates
  batteryPercent?: number
  status: DroneStatus
  missionId?: string
  lastCommunicationAt?: string
  simulated: boolean
}

export interface Observation {
  id: string
  classification: "Confirmed observation" | "Possible observation" | "Unable to verify"
  kind: string
  description: string
  location: Coordinates
  observedAt: string
  source: string
}

export interface Mission {
  id: string
  incidentId: string
  category: EmergencyCategory
  priority: Priority
  objective: string
  area: string
  boundary: Coordinates[]
  hazards: string[]
  instructions: string
  requiredObservations: string[]
  droneId: string
  pilot: string
  createdAt: string
  status: "Awaiting pilot" | "Accepted" | "Preparing" | "In flight" | "Paused" | "Completed" | "Rejected"
  observations: Observation[]
}

export interface DashboardData {
  incidents: Incident[]
  drones: Drone[]
  missions: Mission[]
  unlinkedReports?: CitizenReport[]
  departments?: ResponseDepartment[]
  droneStations?: DroneStation[]
  recentActivity: Array<{ id: string; title: string; detail: string; at: string; tone: "red" | "orange" | "blue" | "green" }>
  simulated: boolean
}

export type RealtimeEvent = {
  type: string
  occurredAt: string
  data: Record<string, unknown>
}
