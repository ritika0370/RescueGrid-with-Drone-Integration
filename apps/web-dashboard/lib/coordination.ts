import { api, isDemoMode, subscribeToEvents } from "@/lib/api"
import { getDemoDashboard } from "@/lib/demo-service"
import type { DashboardData, RealtimeEvent } from "@/shared/types"

export async function loadDashboard(): Promise<DashboardData> {
  if (isDemoMode()) return getDemoDashboard()
  const [incidents, drones, missions, unlinkedReports, departments, droneStations] = await Promise.all([
    api.incidents(), api.drones(), api.jobCards(),
    api.unlinkedReports().catch(() => []),
    api.departments().catch(() => []),
    api.droneStations().catch(() => []),
  ])
  return { incidents, drones, missions, unlinkedReports, departments, droneStations, recentActivity: [], simulated: false }
}

export function connectDashboard(onEvent: (event: RealtimeEvent) => void, onState: (state: "connecting" | "connected" | "disconnected") => void) {
  return subscribeToEvents(onEvent, onState)
}
