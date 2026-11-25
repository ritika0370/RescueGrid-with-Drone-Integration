import type { Metadata } from "next"
import { DashboardShell } from "@/components/dashboard/dashboard-shell"

export const metadata: Metadata = {
  title: "Operations overview | CIRRUS",
  description: "Prototype emergency incident coordination, original citizen reports, and manual drone survey missions.",
}

export default function HomePage() {
  return <DashboardShell />
}
