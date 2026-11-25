import { DEMO_DATA } from "@/shared/demo-data"
import type { DashboardData } from "@/shared/types"

export async function getDemoDashboard(): Promise<DashboardData> {
  return structuredClone(DEMO_DATA)
}

export async function createDemoReport(input: { category: string; description: string; address: string; location: DashboardData["incidents"][number]["location"] }) {
  const stamp = new Date().toISOString()
  return {
    id: `DEMO-RPT-${Math.random().toString(36).slice(2, 8).toUpperCase()}`,
    category: input.category as DashboardData["incidents"][number]["category"],
    description: input.description || "Minimal SOS report",
    address: input.address || "Manually confirmed location",
    location: input.location,
    submittedAt: stamp,
    status: "Submitted" as const,
    media: [],
  }
}
