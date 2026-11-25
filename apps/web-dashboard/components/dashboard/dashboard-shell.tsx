"use client"

import dynamic from "next/dynamic"
import { useCallback, useEffect, useMemo, useState } from "react"
import {
  Activity, AlertOctagon, AlertTriangle, ArrowDownRight, ArrowUpRight, Bell, Check, ChevronDown,
  ChevronRight, ClipboardList, Clock3, CloudLightning, Crosshair, FileText, Flame, MapPin,
  Menu, MessageSquareText, Radio, RefreshCw, Search, Shield, Signal, Siren, Users, Waves,
  X, Zap, type LucideIcon,
} from "lucide-react"
import { api, ApiError, isDemoMode } from "@/lib/api"
import { connectDashboard, loadDashboard } from "@/lib/coordination"
import { BRAND } from "@/shared/design-system"
import type { CitizenReport, DashboardData, Incident, IncidentStatus, Mission, Priority, RealtimeEvent, ResponseDepartment } from "@/shared/types"

const IncidentMap = dynamic(() => import("./incident-map").then((module) => module.IncidentMap), {
  ssr: false,
  loading: () => <div className="map-loading"><span className="loading-dot" /> Loading map tiles…</div>,
})

type PageKey = "overview" | "incidents" | "reports" | "fleet" | "pilot" | "intelligence"
const navigation: Array<{ key: PageKey; label: string; icon: LucideIcon; group: string }> = [
  { key: "overview", label: "Operations overview", icon: Activity, group: "OPERATIONS" },
  { key: "incidents", label: "Incidents", icon: AlertOctagon, group: "OPERATIONS" },
  { key: "reports", label: "Citizen reports", icon: MessageSquareText, group: "OPERATIONS" },
  { key: "fleet", label: "Drone fleet", icon: Crosshair, group: "FIELD ASSETS" },
  { key: "pilot", label: "Pilot workspace", icon: ClipboardList, group: "FIELD ASSETS" },
  { key: "intelligence", label: "Intelligence & reports", icon: FileText, group: "ANALYSIS" },
]

const categoryIcon: Record<string, LucideIcon> = {
  Fire: Flame,
  Flood: Waves,
  Earthquake: Activity,
  "Building collapse": AlertTriangle,
  "Road accident": Shield,
  "Medical emergency": Activity,
  "Missing or trapped person": Users,
  "Other emergency": Siren,
}

const priorityClass: Record<Priority, string> = {
  Critical: "priority-critical",
  High: "priority-high",
  Medium: "priority-medium",
  Low: "priority-low",
}

function formatTime(value: string) {
  return new Intl.DateTimeFormat("en", { hour: "2-digit", minute: "2-digit", hour12: false }).format(new Date(value))
}
function formatDate(value: string) {
  return new Intl.DateTimeFormat("en", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" }).format(new Date(value))
}

function StatusTag({ label, tone = "neutral" }: { label: string; tone?: string }) {
  return <span className={`status-tag status-${tone.replaceAll(" ", "-").toLowerCase()}`}><i />{label}</span>
}

function PriorityTag({ value }: { value: Priority }) {
  return <span className={`priority-tag ${priorityClass[value]}`}><i />{value}</span>
}

function PanelTitle({ title, detail, action }: { title: string; detail?: string; action?: React.ReactNode }) {
  return <div className="panel-title-row"><div><h2>{title}</h2>{detail ? <p>{detail}</p> : null}</div>{action}</div>
}

function StatCard({ label, value, note, tone, icon: Icon, change }: { label: string; value: string | number; note: string; tone: string; icon: LucideIcon; change?: string }) {
  return <article className="stat-card"><div className="stat-card-top"><span>{label}</span><span className={`stat-icon stat-${tone}`}><Icon size={17} strokeWidth={1.9} /></span></div><div className="stat-value">{value}</div><div className="stat-foot"><span className="stat-note">{note}</span>{change ? <span className="stat-change"><ArrowUpRight size={12} />{change}</span> : null}</div></article>
}

function DemoFlag() {
  return <span className="demo-flag"><span />SIMULATED DATA</span>
}

export function DashboardShell() {
  const [page, setPage] = useState<PageKey>("overview")
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [socketState, setSocketState] = useState<"connecting" | "connected" | "disconnected">("disconnected")
  const [mobileNav, setMobileNav] = useState(false)
  const [selectedIncidentId, setSelectedIncidentId] = useState<string | null>(null)
  const [search, setSearch] = useState("")
  const [categoryFilter, setCategoryFilter] = useState("All categories")
  const [priorityFilter, setPriorityFilter] = useState("All priorities")
  const [statusFilter, setStatusFilter] = useState("All statuses")
  const [departmentFilter, setDepartmentFilter] = useState("All departments")
  const [timeFilter, setTimeFilter] = useState("All dates")
  const [toast, setToast] = useState("")
  const [saving, setSaving] = useState(false)
  const demo = isDemoMode()

  const refresh = useCallback(async () => {
    setLoading(true)
    setError("")
    try {
      setData(await loadDashboard())
    } catch (caught) {
      if (!demo && caught instanceof ApiError && caught.status === 401) {
        window.location.replace(`/login?next=${encodeURIComponent(window.location.pathname)}`)
        return
      }
      setError(caught instanceof Error ? caught.message : "Unable to load operations data")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void refresh()
    const unsubscribe = connectDashboard((event: RealtimeEvent) => {
      void refresh()
      setToast(`${event.type.replaceAll("_", " ")} · live update received`)
    }, setSocketState)
    return unsubscribe
  }, [refresh])

  useEffect(() => {
    if (!toast) return
    const timeout = window.setTimeout(() => setToast(""), 4200)
    return () => window.clearTimeout(timeout)
  }, [toast])

  const incidents = data?.incidents ?? []
  const selectedIncident = incidents.find((incident) => incident.id === selectedIncidentId) ?? null
  const filteredIncidents = useMemo(() => incidents.filter((incident) => {
    const term = search.trim().toLowerCase()
    const matchesSearch = !term || [incident.id, incident.title, incident.area, incident.department].some((part) => part.toLowerCase().includes(term))
    const ageLimit = timeFilter === "Past 24 hours" ? 24 * 60 * 60 * 1000 : timeFilter === "Past 7 days" ? 7 * 24 * 60 * 60 * 1000 : Infinity
    const matchesTime = ageLimit === Infinity || Date.now() - new Date(incident.firstReportedAt).getTime() <= ageLimit
    return matchesSearch && matchesTime && (categoryFilter === "All categories" || incident.category === categoryFilter) && (priorityFilter === "All priorities" || incident.priority === priorityFilter) && (statusFilter === "All statuses" || incident.status === statusFilter) && (departmentFilter === "All departments" || incident.department === departmentFilter)
  }), [incidents, search, categoryFilter, priorityFilter, statusFilter, departmentFilter, timeFilter])

  async function updateIncident(incidentId: string, patch: Partial<Incident>) {
    setSaving(true)
    try {
      if (!demo) await api.updateIncident(incidentId, patch)
      setData((current) => current ? { ...current, incidents: current.incidents.map((incident) => incident.id === incidentId ? { ...incident, ...patch, updatedAt: new Date().toISOString() } : incident) } : current)
      setToast(demo ? "Demo state updated · simulated only" : "Incident updated")
    } catch (caught) {
      setToast(caught instanceof Error ? caught.message : "Could not update incident")
    } finally { setSaving(false) }
  }

  async function updateMission(missionId: string, status: Mission["status"], reason?: string) {
    setSaving(true)
    try {
      if (!demo) {
        if (status === "Accepted") await api.acceptMission(missionId)
        else await api.updateMissionStatus(missionId, status, reason)
      }
      setData((current) => current ? { ...current, missions: current.missions.map((mission) => mission.id === missionId ? { ...mission, status } : mission) } : current)
      setToast(demo ? `Demo mission · status set to ${status}` : `Mission status changed to ${status}`)
    } catch (caught) {
      setToast(caught instanceof Error ? caught.message : "Could not update mission")
    } finally { setSaving(false) }
  }

  async function assignIncident(incident: Incident, departmentId: string) {
    setSaving(true)
    try {
      const department = data?.departments?.find((item) => item.id === departmentId)
      if (!demo) {
        await api.assignIncident(incident.id, departmentId)
        await refresh()
      } else {
        await updateIncident(incident.id, { status: "Assigned", departmentId, department: department?.name || departmentId })
      }
      setPage("incidents")
      setToast(demo ? "Demo assignment updated · simulated only" : "Incident assigned")
    } catch (caught) { setToast(caught instanceof Error ? caught.message : "Could not assign incident") }
    finally { setSaving(false) }
  }

  async function reviewGrouping(incidentId: string, decision: "confirm" | "reject") {
    try {
      if (!demo) await api.reviewGrouping(incidentId, decision)
      setToast(demo ? `Grouping ${decision} recorded for this session · simulated only` : `Grouping suggestion ${decision}ed`)
    } catch (caught) { setToast(caught instanceof Error ? caught.message : "Could not review grouping") }
  }

  async function linkReportToIncident(incidentId: string, reportId: string) {
    const report = data?.unlinkedReports?.find((item) => item.id === reportId)
    if (!report) { setToast("That source report is no longer available to link"); return }
    try {
      if (!demo) {
        await api.linkReport(incidentId, reportId)
        await refresh()
      } else {
        setData((current) => current ? {
          ...current,
          unlinkedReports: (current.unlinkedReports || []).filter((item) => item.id !== reportId),
          incidents: current.incidents.map((item) => item.id === incidentId ? { ...item, linkedReports: [...item.linkedReports, { ...report, incidentId }] } : item),
        } : current)
      }
      setToast(demo ? "Report linked · simulated session only; original source retained" : "Report linked to incident")
    } catch (caught) { setToast(caught instanceof Error ? caught.message : "Could not link report") }
  }

  async function unlinkReportFromIncident(incidentId: string, reportId: string) {
    const report = data?.incidents.find((item) => item.id === incidentId)?.linkedReports.find((item) => item.id === reportId)
    if (!report) return
    try {
      if (!demo) {
        await api.unlinkReport(incidentId, reportId)
        await refresh()
      } else {
        setData((current) => current ? {
          ...current,
          unlinkedReports: [...(current.unlinkedReports || []), { ...report, incidentId: undefined }],
          incidents: current.incidents.map((item) => item.id === incidentId ? { ...item, linkedReports: item.linkedReports.filter((source) => source.id !== reportId) } : item),
        } : current)
      }
      setToast(demo ? "Report unlinked · original source record preserved" : "Report unlinked from incident")
    } catch (caught) { setToast(caught instanceof Error ? caught.message : "Could not unlink report") }
  }

  async function createMission(incident: Incident) {
    setSaving(true)
    try {
      const existing = data?.missions.find((mission) => mission.incidentId === incident.id)
      if (existing) { setPage("pilot"); return }
      const payload: Partial<Mission> = {
        incidentId: incident.id, category: incident.category, priority: incident.priority,
        objective: `Survey ${incident.area}; report safe access, visible hazards, and observations requiring responder review.`,
        area: incident.area, boundary: [], hazards: incident.hazards, instructions: "Coordinate with the incident officer. No flight control is available in this dashboard.",
        requiredObservations: ["Visible hazard extent", "Safe access route", "Areas requiring ground review"],
        droneId: "DR-12", pilot: "Unassigned", status: "Awaiting pilot", observations: [],
      }
      const created = demo ? { ...payload, id: `DEMO-MSN-${Date.now().toString().slice(-4)}`, createdAt: new Date().toISOString() } as Mission : await api.createJobCard(incident.id, payload)
      setData((current) => current ? { ...current, missions: [created, ...current.missions] } : current)
      setPage("pilot")
      setToast(demo ? "Demo job card created · simulated only" : "Survey job card created")
    } catch (caught) { setToast(caught instanceof Error ? caught.message : "Could not create mission") }
    finally { setSaving(false) }
  }

  const pageTitle = navigation.find((item) => item.key === page)?.label || "Operations overview"
  const criticalCount = incidents.filter((item) => item.priority === "Critical" && item.status !== "Resolved" && item.status !== "Closed").length
  const highCount = incidents.filter((item) => item.priority === "High" && item.status !== "Resolved" && item.status !== "Closed").length
  const reviewCount = incidents.filter((item) => item.status === "Under review").length
  const activeMissions = data?.missions.filter((mission) => ["Accepted", "Preparing", "In flight", "Paused"].includes(mission.status)).length ?? 0

  return (
    <div className="ops-app">
      {mobileNav ? <button className="sidebar-backdrop" aria-label="Close navigation" onClick={() => setMobileNav(false)} /> : null}
      <aside className={`ops-sidebar ${mobileNav ? "sidebar-open" : ""}`}>
        <a className="brand-lockup" href="/" aria-label="CIRRUS response coordination home"><span className="brand-mark"><span /></span><span><strong>CIRRUS</strong><small>RESPONSE COORDINATION</small></span></a>
        <div className="sidebar-environment"><span className="environment-dot" /><span>PROTOTYPE WORKSPACE</span></div>
        <div className="sidebar-nav">
          {navigation.map((item, index) => {
            const Previous = navigation[index - 1]
            return <div key={item.key}>{(!Previous || Previous.group !== item.group) ? <div className="nav-group-label">{item.group}</div> : null}<button className={`nav-link ${page === item.key ? "nav-active" : ""}`} onClick={() => { setPage(item.key); setMobileNav(false); setSelectedIncidentId(null) }}><item.icon size={17} strokeWidth={1.8} /><span>{item.label}</span>{item.key === "incidents" && criticalCount > 0 ? <span className="nav-count">{criticalCount}</span> : null}</button></div>
          })}
        </div>
        <div className="sidebar-bottom"><div className="sidebar-help-icon"><Shield size={16} /></div><div><strong>Response desk</strong><small>Prototype · no dispatch</small></div><a href="/login" className="profile-link" aria-label="Open sign-in page"><ChevronDown size={16} /></a></div>
      </aside>

      <div className="ops-main">
        <header className="ops-topbar">
          <div className="topbar-left"><button className="mobile-menu-button" aria-label="Open navigation" onClick={() => setMobileNav(true)}><Menu size={20} /></button><span className="breadcrumb-root">Operations</span><ChevronRight size={14} /><span className="breadcrumb-current">{pageTitle}</span></div>
          <div className="topbar-right"><div className={`connection-pill connection-${socketState}`}><span />{socketState === "connected" ? "Live updates" : socketState === "connecting" ? "Connecting" : "Realtime offline"}</div><button className="icon-button" aria-label="Notifications are not configured" disabled><Bell size={17} /></button><div className="profile-avatar">RO</div><div className="profile-summary"><strong>Response desk</strong><span>{demo ? "Demo · simulated identity" : "Authenticated session · backend permissions"}</span></div></div>
        </header>

        <main className="ops-content">
          <div className="page-heading"><div><div className="eyebrow-label">{page === "overview" ? new Intl.DateTimeFormat("en", { weekday: "long", month: "long", day: "numeric" }).format(new Date()).toUpperCase() : "RESPONSE COORDINATION"}</div><h1>{page === "overview" ? "Operations overview" : pageTitle}</h1><p>{pageDescription(page)}</p></div><div className="heading-actions">{demo || data?.simulated ? <DemoFlag /> : null}<button className="quiet-button" onClick={() => void refresh()} disabled={loading}><RefreshCw size={14} className={loading ? "spin" : ""} />Refresh</button></div></div>

          {error ? <div className="error-banner" role="alert"><AlertTriangle size={17} /><span>Backend connection unavailable: {error}</span><button onClick={() => void refresh()}>Retry</button></div> : null}
          {loading && !data ? <div className="loading-panel"><span className="loading-dot" />Connecting to the coordination service…</div> : null}
          {data && page === "overview" ? <OverviewPage data={data} realtimeStatus={socketState} criticalCount={criticalCount} highCount={highCount} reviewCount={reviewCount} activeMissions={activeMissions} selectedId={selectedIncidentId || undefined} onSelect={(id) => { setSelectedIncidentId(id); setPage("incidents") }} onIncident={(incident) => { setSelectedIncidentId(incident.id); setPage("incidents") }} /> : null}
          {data && page === "incidents" ? <IncidentsPage data={data} incidents={filteredIncidents} selectedIncident={selectedIncident} selectedId={selectedIncidentId} onSearch={setSearch} search={search} categoryFilter={categoryFilter} setCategoryFilter={setCategoryFilter} priorityFilter={priorityFilter} setPriorityFilter={setPriorityFilter} statusFilter={statusFilter} setStatusFilter={setStatusFilter} departmentFilter={departmentFilter} setDepartmentFilter={setDepartmentFilter} timeFilter={timeFilter} setTimeFilter={setTimeFilter} onSelect={(id) => setSelectedIncidentId(id || null)} onUpdate={updateIncident} onAssign={assignIncident} onCreateMission={createMission} onLinkReport={linkReportToIncident} onUnlinkReport={unlinkReportFromIncident} onGroupingReview={reviewGrouping} saving={saving} /> : null}
          {data && page === "reports" ? <ReportsPage reports={[...data.incidents.flatMap((incident) => incident.linkedReports), ...(data.unlinkedReports || [])]} onIncident={(id) => { setSelectedIncidentId(id); setPage("incidents") }} incidents={data.incidents} /> : null}
          {data && page === "fleet" ? <FleetPage data={data} /> : null}
          {data && page === "pilot" ? <PilotPage data={data} saving={saving} onMissionStatus={updateMission} /> : null}
          {data && page === "intelligence" ? <IntelligencePage data={data} onIncident={(id) => { setSelectedIncidentId(id); setPage("incidents") }} /> : null}
          <footer className="ops-footer"><span>Prototype only · Not affiliated with an official agency</span><span>{demo || data?.simulated ? "SIMULATED MAP & TELEMETRY" : "BACKEND DATA · VERIFY SOURCE"} <i /></span></footer>
        </main>
      </div>
      {toast ? <div className="toast-message" role="status"><Check size={15} />{toast}<button onClick={() => setToast("")} aria-label="Dismiss message"><X size={14} /></button></div> : null}
    </div>
  )
}

function pageDescription(page: PageKey) {
  const descriptions: Record<PageKey, string> = {
    overview: "A shared, situational view of reports, response activity, and field assets.",
    incidents: "Review linked reports while preserving each citizen's original submission and location.",
    reports: "Incoming citizen reports, source evidence, and backend-confirmed status.",
    fleet: "Registered assets and backend-provided availability; no flight controls are available.",
    pilot: "Assigned manual survey missions, job cards, and pilot-submitted field observations.",
    intelligence: "Source-attributed field data and clearly separated advisory analysis.",
  }
  return descriptions[page]
}

function OverviewPage({ data, realtimeStatus, criticalCount, highCount, reviewCount, activeMissions, selectedId, onSelect, onIncident }: {
  data: DashboardData; realtimeStatus: "connecting" | "connected" | "disconnected"; criticalCount: number; highCount: number; reviewCount: number; activeMissions: number; selectedId?: string; onSelect: (id: string) => void; onIncident: (incident: Incident) => void
}) {
  const active = data.incidents.filter((incident) => incident.status !== "Resolved" && incident.status !== "Closed")
  const linkedReports = data.incidents.reduce((total, incident) => total + incident.linkedReports.length, 0)
  const resolved = data.incidents.filter((incident) => incident.status === "Resolved").length
  return <>
    <section className="stat-grid">
      <StatCard label="Active incidents" value={active.length} note={`${linkedReports} linked citizen reports`} tone="blue" icon={Activity} change={data.simulated ? "+2 today · demo" : undefined} />
      <StatCard label="Critical" value={criticalCount} note="Requires officer review" tone="red" icon={AlertOctagon} />
      <StatCard label="High priority" value={highCount} note="Active high-priority cases" tone="orange" icon={AlertTriangle} />
      <StatCard label="Awaiting review" value={reviewCount} note="Incident grouping unconfirmed" tone="yellow" icon={Clock3} />
      <StatCard label="Survey missions" value={activeMissions} note={data.simulated ? "Manual pilot · simulated" : "Manual pilot missions"} tone="cyan" icon={Crosshair} />
      <StatCard label="Resolved" value={resolved} note={data.simulated ? "In current demo data" : "Resolved incidents"} tone="green" icon={Check} />
    </section>

    <section className="overview-grid">
      <article className="panel map-panel"><PanelTitle title="Incident map" detail="Reports, incident groups, departments, stations, and assets" action={<span className={`map-live-tag ${data.simulated ? "" : "map-live"}`}><span />{data.simulated ? "SIMULATED" : "BACKEND DATA"}</span>} />
        <div className="map-wrap"><IncidentMap incidents={data.incidents} drones={data.drones} missions={data.missions} selectedId={selectedId} onSelect={onSelect} departments={data.departments} droneStations={data.droneStations} unlinkedReports={data.unlinkedReports} /><span className="map-attribution-note">© OpenStreetMap contributors{data.simulated ? " · simulated records" : " · source locations shown"}</span></div>
        <div className="map-legend"><span><i className="legend-dot red" />Fire</span><span><i className="legend-dot blue" />Flood</span><span><i className="legend-dot orange" />Collapse</span><span><i className="legend-dot gray" />Citizen report</span><span><i className="legend-dot cyan" />Drone</span><span className="map-count">{active.length} active</span></div>
      </article>
      <article className="panel activity-panel"><PanelTitle title="Recent activity" detail={data.simulated ? "Updates from this prototype dataset" : "Backend incident events"} action={<button className="text-button" aria-label="View incident list" onClick={() => data.incidents[0] && onIncident(data.incidents[0])}>View all <ChevronRight size={13} /></button>} />
        {data.recentActivity.length ? <div className="activity-list">{data.recentActivity.map((activity) => <div className="activity-item" key={activity.id}><span className={`activity-indicator activity-${activity.tone}`}><Activity size={13} /></span><div className="activity-copy"><strong>{activity.title}</strong><span>{activity.detail}</span></div><time>{activity.at}</time></div>)}</div> : <div className="empty-activity">No recent activity has been returned by the backend.</div>}
        <div className="activity-divider" /><div className="radio-status"><div className="radio-icon"><Radio size={15} /></div><div><strong>Realtime channel</strong><span>{data.simulated ? "Simulated data · WebSocket disabled" : realtimeStatus === "connected" ? "WebSocket connected · live events enabled" : realtimeStatus === "connecting" ? "Connecting to configured WebSocket" : "WebSocket disconnected"}</span></div><span className={`offline-pill ${realtimeStatus === "connected" ? "online-pill" : ""}`}>{realtimeStatus === "connected" ? "LIVE" : "OFFLINE"}</span></div>
      </article>
    </section>

    <section className="lower-grid">
      <article className="panel incident-queue"><PanelTitle title="Priority incidents" detail="Grouped incidents preserve individual report locations" action={<button className="text-button" onClick={() => onIncident(data.incidents[0])}>All incidents <ChevronRight size={13} /></button>} />
        <div className="incident-table-wrap"><table className="incident-table"><thead><tr><th>INCIDENT</th><th>PRIORITY</th><th>REPORTS</th><th>STATUS</th><th>UPDATED</th><th /></tr></thead><tbody>{active.map((incident) => <IncidentTableRow key={incident.id} incident={incident} onClick={() => onIncident(incident)} />)}</tbody></table></div>
      </article>
      <article className="panel trend-panel"><PanelTitle title="Response activity" detail={data.simulated ? "Sampled reports · simulated" : "Report trend · backend data"} action={<span className="period-label">LAST 6 HOURS <ChevronDown size={12} /></span>} />
        <div className="trend-total"><strong>{linkedReports}</strong><span>citizen reports in sample</span></div>
        <div className="trend-chart" role="img" aria-label="Illustrative six-hour simulated report activity bar chart">{[{ h: 25, label: "09" }, { h: 36, label: "10" }, { h: 31, label: "11" }, { h: 53, label: "12" }, { h: 72, label: "13" }, { h: 91, label: "14" }].map((point, i) => <div className="trend-column" key={point.label}><div className="trend-bar-stack"><i style={{ height: `${point.h * 0.66}%` }} /><i style={{ height: `${point.h * 0.34}%` }} /><i style={{ height: `${Math.max(3, 100 - point.h)}%` }} /></div><span>{point.label}</span></div>)}</div>
        <div className="trend-key"><span><i className="red" />Critical</span><span><i className="orange" />High</span><span><i className="slate" />Other</span></div>
      </article>
    </section>
  </>
}

function IncidentTableRow({ incident, onClick }: { incident: Incident; onClick: () => void }) {
  const CategoryIcon = categoryIcon[incident.category] || AlertTriangle
  return <tr onClick={onClick} tabIndex={0} onKeyDown={(event) => { if (event.key === "Enter") onClick() }}>
    <td><div className="incident-name"><span className={`category-icon icon-${incident.category.toLowerCase().replaceAll(" ", "-")}`}><CategoryIcon size={14} /></span><span><strong>{incident.id}</strong><small>{incident.title}</small></span></div></td>
    <td><PriorityTag value={incident.priority} /></td><td><span className="report-count"><Users size={13} />{incident.linkedReports.length}</span></td><td><StatusTag label={incident.status} tone={incident.status} /></td><td className="table-time">{formatTime(incident.updatedAt)}</td><td><ChevronRight size={15} className="row-chevron" /></td>
  </tr>
}

function FilterBar({ search, onSearch, categoryFilter, setCategoryFilter, priorityFilter, setPriorityFilter, statusFilter, setStatusFilter, departmentFilter, setDepartmentFilter, timeFilter, setTimeFilter, departments }: {
  search: string; onSearch: (value: string) => void; categoryFilter: string; setCategoryFilter: (value: string) => void; priorityFilter: string; setPriorityFilter: (value: string) => void; statusFilter: string; setStatusFilter: (value: string) => void; departmentFilter: string; setDepartmentFilter: (value: string) => void; timeFilter: string; setTimeFilter: (value: string) => void; departments: string[]
}) {
  return <div className="filter-bar"><label className="search-field"><Search size={15} /><input placeholder="Search incident, area, or geographic area" value={search} onChange={(event) => onSearch(event.target.value)} aria-label="Search incidents and geographic area" /></label>
    <label className="filter-select-label"><span className="sr-only">Filter by category</span><select value={categoryFilter} onChange={(event) => setCategoryFilter(event.target.value)}><option>All categories</option>{["Fire", "Flood", "Earthquake", "Building collapse", "Road accident", "Medical emergency", "Missing or trapped person", "Other emergency"].map((value) => <option key={value}>{value}</option>)}</select></label>
    <label className="filter-select-label"><span className="sr-only">Filter by priority</span><select value={priorityFilter} onChange={(event) => setPriorityFilter(event.target.value)}><option>All priorities</option>{["Critical", "High", "Medium", "Low"].map((value) => <option key={value}>{value}</option>)}</select></label>
    <label className="filter-select-label"><span className="sr-only">Filter by status</span><select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}><option>All statuses</option>{["Under review", "Confirmed", "Assigned", "Survey in progress", "Rescue team notified", "Resolved", "Closed"].map((value) => <option key={value}>{value}</option>)}</select></label>
    <label className="filter-select-label"><span className="sr-only">Filter by department</span><select value={departmentFilter} onChange={(event) => setDepartmentFilter(event.target.value)}><option>All departments</option>{departments.map((value) => <option key={value}>{value}</option>)}</select></label>
    <label className="filter-select-label"><span className="sr-only">Filter by date</span><select value={timeFilter} onChange={(event) => setTimeFilter(event.target.value)}><option>All dates</option><option>Past 24 hours</option><option>Past 7 days</option></select></label></div>
}

function IncidentsPage({ data, incidents, selectedIncident, selectedId, onSearch, search, categoryFilter, setCategoryFilter, priorityFilter, setPriorityFilter, statusFilter, setStatusFilter, departmentFilter, setDepartmentFilter, timeFilter, setTimeFilter, onSelect, onUpdate, onAssign, onCreateMission, onLinkReport, onUnlinkReport, onGroupingReview, saving }: {
  data: DashboardData; incidents: Incident[]; selectedIncident: Incident | null; selectedId: string | null; search: string; onSearch: (value: string) => void; categoryFilter: string; setCategoryFilter: (value: string) => void; priorityFilter: string; setPriorityFilter: (value: string) => void; statusFilter: string; setStatusFilter: (value: string) => void; departmentFilter: string; setDepartmentFilter: (value: string) => void; timeFilter: string; setTimeFilter: (value: string) => void; onSelect: (id: string) => void; onUpdate: (id: string, patch: Partial<Incident>) => void; onAssign: (incident: Incident, departmentId: string) => void; onCreateMission: (incident: Incident) => void; onLinkReport: (incidentId: string, reportId: string) => void; onUnlinkReport: (incidentId: string, reportId: string) => void; onGroupingReview: (incidentId: string, decision: "confirm" | "reject") => void; saving: boolean
}) {
  return <div className={`incident-workspace ${selectedIncident ? "has-detail" : ""}`}>
    <section className="panel incident-list-panel"><PanelTitle title="Incident queue" detail={`${incidents.length} matching incidents · ${data.incidents.flatMap((item) => item.linkedReports).length + (data.unlinkedReports?.length || 0)} source reports`} action={<span className="queue-dot"><span />QUEUE ACTIVE</span>} /><FilterBar search={search} onSearch={onSearch} categoryFilter={categoryFilter} setCategoryFilter={setCategoryFilter} priorityFilter={priorityFilter} setPriorityFilter={setPriorityFilter} statusFilter={statusFilter} setStatusFilter={setStatusFilter} departmentFilter={departmentFilter} setDepartmentFilter={setDepartmentFilter} timeFilter={timeFilter} setTimeFilter={setTimeFilter} departments={[...new Set(data.incidents.map((item) => item.department))]} /><div className="incident-table-wrap"><table className="incident-table full-table"><thead><tr><th>INCIDENT / AREA</th><th>PRIORITY</th><th>REPORTS</th><th>PEOPLE*</th><th>DEPARTMENT</th><th>STATUS</th><th>LAST UPDATED</th></tr></thead><tbody>{incidents.map((incident) => <tr key={incident.id} className={selectedId === incident.id ? "row-selected" : ""} onClick={() => onSelect(incident.id)} tabIndex={0} onKeyDown={(event) => { if (event.key === "Enter") onSelect(incident.id) }}><td><div className="incident-name"><span className="category-icon"><span>{incident.category.slice(0, 1)}</span></span><span><strong>{incident.id}</strong><small>{incident.area}</small></span></div></td><td><PriorityTag value={incident.priority} /></td><td>{incident.linkedReports.length}</td><td>{incident.peopleAffected ?? "—"} <small className="subtle-count">/ {incident.peopleTrapped ?? "—"} trapped</small></td><td>{incident.department}</td><td><StatusTag label={incident.status} tone={incident.status} /></td><td className="table-time">{formatDate(incident.updatedAt)}</td></tr>)}</tbody></table>{incidents.length === 0 ? <div className="empty-state"><Search size={19} /><strong>No matching incidents</strong><span>Try clearing one or more filters.</span></div> : null}</div><div className="table-footnote">*People counts are unverified report estimates. Grouping and identity must be reviewed by authorized responders.</div></section>
    {selectedIncident ? <IncidentDetail key={selectedIncident.id} incident={selectedIncident} onClose={() => onSelect("")} onUpdate={onUpdate} onAssign={onAssign} onCreateMission={onCreateMission} onLinkReport={onLinkReport} onUnlinkReport={onUnlinkReport} onGroupingReview={onGroupingReview} unlinkedReports={data.unlinkedReports || []} departments={data.departments || []} missionExists={data.missions.some((mission) => mission.incidentId === selectedIncident.id)} saving={saving} /> : <article className="panel detail-empty"><div className="empty-icon"><MapPin size={20} /></div><strong>Select an incident</strong><span>Review linked citizen reports, locations, and updates.</span></article>}
  </div>
}

function IncidentDetail({ incident, onClose, onUpdate, onAssign, onCreateMission, onLinkReport, onUnlinkReport, onGroupingReview, unlinkedReports, departments, missionExists, saving }: {
  incident: Incident; onClose: () => void; onUpdate: (id: string, patch: Partial<Incident>) => void; onAssign: (incident: Incident, departmentId: string) => void; onCreateMission: (incident: Incident) => void; onLinkReport: (incidentId: string, reportId: string) => void; onUnlinkReport: (incidentId: string, reportId: string) => void; onGroupingReview: (incidentId: string, decision: "confirm" | "reject") => void; unlinkedReports: CitizenReport[]; departments: ResponseDepartment[]; missionExists: boolean; saving: boolean
}) {
  const [note, setNote] = useState("")
  const [showNoteForm, setShowNoteForm] = useState(false)
  const [departmentId, setDepartmentId] = useState(incident.departmentId || departments[0]?.id || incident.department)
  const [reportToLink, setReportToLink] = useState(unlinkedReports[0]?.id || "")
  const [groupingDecision, setGroupingDecision] = useState<"confirm" | "reject" | "">("")
  const departmentOptions = departments.length ? departments : [{ id: incident.departmentId || incident.department, name: incident.department, location: incident.location }]
  return <aside className="panel incident-detail-panel" aria-label={`Details for ${incident.id}`}>
    <div className="detail-header"><div><div className="detail-id">{incident.id} <DemoFlag /></div><h2>{incident.title}</h2><p><MapPin size={13} />{incident.area}</p></div><button className="icon-button detail-close" onClick={onClose} aria-label="Close incident details"><X size={17} /></button></div>
    <div className="detail-tags"><PriorityTag value={incident.priority} /><StatusTag label={incident.status} tone={incident.status} /></div>
    <div className="detail-map"><IncidentMap incidents={[incident]} drones={[]} missions={[]} selectedId={incident.id} /></div>
    <div className="detail-facts"><div><span>First reported</span><strong>{formatDate(incident.firstReportedAt)}</strong></div><div><span>Linked reports</span><strong>{incident.linkedReports.length} individual locations</strong></div><div><span>People estimates</span><strong>{incident.peopleAffected ?? "Unknown"} affected · {incident.peopleTrapped ?? "Unknown"} trapped</strong></div><div><span>Assigned department</span><strong>{incident.department}</strong></div></div>
    <div className="detail-section"><div className="section-label">SITUATION SUMMARY <span>ADVISORY</span></div><p className="summary-copy">{incident.summary}</p><div className="confidence-track"><span style={{ width: `${incident.confidence * 100}%` }} /></div><span className="confidence-caption">Model confidence {Math.round(incident.confidence * 100)}% · Requires human review</span></div>
    <div className="detail-section"><div className="section-label">POTENTIAL HAZARDS</div><div className="hazard-list">{incident.hazards.map((hazard) => <span key={hazard}><AlertTriangle size={12} />{hazard}</span>)}</div></div>
    <div className="detail-section"><div className="section-label">CITIZEN REPORTS <span>{incident.linkedReports.length} SOURCES</span></div><p className="grouping-disclaimer">Grouping suggestions are advisory. Linking never merges or overwrites original reports.</p><div className="group-review-actions"><button className={`outline-action ${groupingDecision === "confirm" ? "action-selected" : ""}`} onClick={() => { setGroupingDecision("confirm"); onGroupingReview(incident.id, "confirm") }}>Confirm grouping</button><button className={`outline-action ${groupingDecision === "reject" ? "action-selected" : ""}`} onClick={() => { setGroupingDecision("reject"); onGroupingReview(incident.id, "reject") }}>Reject suggestion</button></div><div className="source-report-list">{incident.linkedReports.map((report) => <div className="source-report-with-action" key={report.id}><SourceReport report={report} /><button className="text-button unlink-report" onClick={() => onUnlinkReport(incident.id, report.id)}>Unlink report</button></div>)}</div><form className="link-report-form" onSubmit={(event) => { event.preventDefault(); if (reportToLink) { onLinkReport(incident.id, reportToLink); setReportToLink("") } }}><label><span>Link another source report</span><select aria-label="Select a source report to link" value={reportToLink} onChange={(event) => setReportToLink(event.target.value)}><option value="">Choose an unlinked report</option>{unlinkedReports.map((report) => <option key={report.id} value={report.id}>{report.id} · {report.category}</option>)}</select></label><button className="outline-action" type="submit" disabled={!reportToLink}>Link report</button></form></div>
    <div className="detail-section"><div className="section-label">DEPARTMENT NOTES <button className="text-button" onClick={() => setShowNoteForm((current) => !current)}><MessageSquareText size={12} /> Add note</button></div>{incident.notes.length ? incident.notes.map((item) => <p className="note-entry" key={item}>{item}</p>) : <p className="empty-inline">No internal notes have been added.</p>}{showNoteForm ? <form className="note-form" onSubmit={(event) => { event.preventDefault(); if (note.trim()) { onUpdate(incident.id, { notes: [...incident.notes, `${new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })} · ${note.trim()} — Response officer (demo)`] }); setNote(""); setShowNoteForm(false) } }}><input value={note} onChange={(event) => setNote(event.target.value)} placeholder="Add internal note" aria-label="Internal incident note" /><button aria-label="Save note"><Check size={14} /></button></form> : null}</div>
    <div className="detail-section action-section"><div className="section-label">OFFICER ACTIONS <span>BACKEND AUTHORIZED</span></div><label className="detail-select-label">Priority<select value={incident.priority} onChange={(event) => onUpdate(incident.id, { priority: event.target.value as Priority })}><option>Critical</option><option>High</option><option>Medium</option><option>Low</option></select></label><label className="detail-select-label">Incident status<select value={incident.status} onChange={(event) => onUpdate(incident.id, { status: event.target.value as IncidentStatus })}><option>Under review</option><option>Confirmed</option><option>Assigned</option><option>Survey in progress</option><option>Rescue team notified</option><option>Resolved</option><option>Closed</option></select></label><label className="detail-select-label">Assign department<select value={departmentId} onChange={(event) => setDepartmentId(event.target.value)}>{departmentOptions.map((department) => <option key={department.id} value={department.id}>{department.name}</option>)}</select></label><button className="outline-action" disabled={saving || !departmentId} onClick={() => onAssign(incident, departmentId)}><Users size={14} />Assign to department</button><button className="primary-action" disabled={saving} onClick={() => onCreateMission(incident)}><Crosshair size={14} />{missionExists ? "Open survey job card" : "Create drone survey job card"}</button><p className="action-note">Assignment and mission creation require backend permission checks. No flight controls are provided.</p></div>
  </aside>
}

function SourceReport({ report }: { report: CitizenReport }) {
  return <article className="source-report"><div className="source-top"><strong>{report.id}</strong><time>{formatTime(report.submittedAt)}</time></div><span className="source-location"><MapPin size={11} />{report.address} · {report.location.source === "simulated" ? "simulated location" : report.location.source}</span><p>{report.description}</p><div className="source-meta"><StatusTag label={report.status} tone={report.status} />{report.media.length ? <span><FileText size={11} />{report.media.length} attachment</span> : null}{report.peopleTrapped ? <span><Users size={11} />{report.peopleTrapped} possibly trapped · unverified</span> : null}</div>{report.media.length ? <div className="report-media-grid">{report.media.map((media) => media.type === "image" ? <img key={media.id} src={media.url} alt={`${media.label} · simulated image`} /> : <span key={media.id}>{media.label}</span>)}</div> : null}</article>
}

function ReportsPage({ reports, incidents, onIncident }: { reports: CitizenReport[]; incidents: Incident[]; onIncident: (id: string) => void }) {
  return <section className="panel reports-panel"><PanelTitle title="Incoming reports" detail="Original submissions are retained independently from incident grouping" action={<span className="queue-dot"><span />{reports.length} REPORTS</span>} />{reports.length ? <div className="report-cards">{reports.map((report) => { const incident = incidents.find((item) => item.id === report.incidentId); return <article className="report-card" key={report.id}><div className="report-card-top"><div><span className="report-id">{report.id}</span><h3>{report.category}</h3></div><StatusTag label={report.status} tone={report.status} /></div><p>{report.description}</p><div className="report-card-meta"><span><MapPin size={13} />{report.address}</span><span><Clock3 size={13} />{formatDate(report.submittedAt)}</span><span><Users size={13} />{report.peopleAffected ?? "—"} affected · {report.peopleTrapped ?? "—"} trapped</span></div><div className="report-card-bottom"><span>Individual location · {report.location.latitude.toFixed(4)}, {report.location.longitude.toFixed(4)}</span>{incident ? <button className="text-button" onClick={() => onIncident(incident.id)}>Open {incident.id} <ChevronRight size={13} /></button> : <span>Not linked to an incident · original report preserved</span>}</div></article> })}</div> : <div className="empty-state"><FileText size={19} /><strong>No citizen reports returned</strong><span>New backend reports will appear here.</span></div>}<div className="data-integrity-note"><Shield size={14} /><span>Every citizen report remains a separate source record. Linking reports does not overwrite the original text, media, timestamps, or locations.</span></div></section>
}

function FleetPage({ data }: { data: DashboardData }) {
  return <><div className="fleet-callout"><div className="fleet-callout-icon"><Signal size={17} /></div><div><strong>Backend telemetry only</strong><span>Asset status and location below come from the selected data source. Demo telemetry is simulated—not live.</span></div><DemoFlag /></div><section className="drone-grid">{data.drones.map((drone) => <article className="panel drone-card" key={drone.id}><div className="drone-card-head"><span className="drone-glyph"><Crosshair size={19} /></span><StatusTag label={drone.status} tone={drone.status} /></div><div className="drone-name"><strong>{drone.id}</strong><span>{drone.model}</span></div><div className="drone-station"><MapPin size={13} />{drone.station}</div><div className="drone-battery"><div className="battery-meta"><span>Battery</span><strong>{drone.batteryPercent == null ? "Unavailable" : `${drone.batteryPercent}%`}</strong></div><div className="battery-track"><i style={{ width: `${drone.batteryPercent ?? 0}%` }} className={(drone.batteryPercent ?? 0) < 25 ? "battery-low" : ""} /></div></div><div className="drone-info"><div><span>Current mission</span><strong>{drone.missionId || "None"}</strong></div><div><span>Last communication</span><strong>{drone.lastCommunicationAt ? formatTime(drone.lastCommunicationAt) : "Unknown"}</strong></div></div><div className="drone-note">{drone.simulated ? "SIMULATED RECORD · not live telemetry" : "Reported by backend"}</div></article>)}</section><section className="panel fleet-map-panel"><PanelTitle title="Fleet and mission area" detail="Location markers reflect backend or clearly simulated telemetry" /><div className="fleet-map"><IncidentMap incidents={data.incidents} drones={data.drones} missions={data.missions} /></div></section></>
}

function PilotPage({ data, saving, onMissionStatus }: { data: DashboardData; saving: boolean; onMissionStatus: (id: string, status: Mission["status"], reason?: string) => void }) {
  const [openMission, setOpenMission] = useState(data.missions[0]?.id ?? "")
  const [finding, setFinding] = useState("")
  const [classification, setClassification] = useState("Possible observation")
  const [uploadMessage, setUploadMessage] = useState("")
  const [mode, setMode] = useState<"manual" | "autonomous">("manual")
  return <><div className="pilot-mode-bar"><div className="mode-label"><span className="mode-icon"><Crosshair size={17} /></span><span><strong>Mission mode</strong><small>Only manually piloted survey is enabled</small></span></div><div className="mode-selector"><button className={mode === "manual" ? "mode-selected" : ""} onClick={() => setMode("manual")}>Manual pilot</button><button disabled className="mode-disabled" title="Future capability · not implemented or authorized">Autonomous · future</button></div></div><div className="pilot-layout"><section className="panel mission-queue"><PanelTitle title="Assigned missions" detail={`${data.missions.length} job cards · backend permissions apply`} />{data.missions.length ? data.missions.map((mission) => <button key={mission.id} className={`mission-queue-item ${openMission === mission.id ? "mission-selected" : ""}`} onClick={() => setOpenMission(mission.id)}><span className="mission-state-marker" /><span className="mission-queue-copy"><strong>{mission.id}</strong><small>{mission.category} · {mission.area}</small></span><PriorityTag value={mission.priority} /></button>) : <div className="empty-state"><Crosshair size={19} /><strong>No assigned missions</strong><span>Assigned job cards will appear here.</span></div>}</section>{data.missions.filter((mission) => mission.id === openMission).map((mission) => <PilotMission key={mission.id} mission={mission} saving={saving} finding={finding} setFinding={setFinding} classification={classification} setClassification={setClassification} uploadMessage={uploadMessage} setUploadMessage={setUploadMessage} onMissionStatus={onMissionStatus} />)}</div></>
}

function PilotMission({ mission, saving, finding, setFinding, classification, setClassification, uploadMessage, setUploadMessage, onMissionStatus }: {
  mission: Mission; saving: boolean; finding: string; setFinding: (value: string) => void; classification: string; setClassification: (value: string) => void; uploadMessage: string; setUploadMessage: (value: string) => void; onMissionStatus: (id: string, status: Mission["status"], reason?: string) => void
}) {
  return <section className="panel mission-detail"><div className="mission-detail-head"><div><div className="mission-id-label">JOB CARD · {mission.id}</div><h2>{mission.area}</h2><p>{mission.incidentId} · {mission.category} · <PriorityTag value={mission.priority} /></p></div><StatusTag label={mission.status} tone={mission.status} /></div><div className="mission-map"><IncidentMap incidents={[]} drones={[]} missions={[mission]} /></div><div className="mission-facts"><div><span>Mission objective</span><strong>{mission.objective}</strong></div><div><span>Assigned asset</span><strong>{mission.droneId}</strong></div><div><span>Assigned pilot</span><strong>{mission.pilot}</strong></div><div><span>Mission created</span><strong>{formatDate(mission.createdAt)}</strong></div></div><div className="detail-section"><div className="section-label">SURVEY INSTRUCTIONS</div><p className="summary-copy">{mission.instructions}</p><ul className="mission-checklist">{mission.requiredObservations.map((item) => <li key={item}><Check size={13} />{item}</li>)}</ul></div><div className="detail-section"><div className="section-label">KNOWN HAZARDS</div><div className="hazard-list">{mission.hazards.map((hazard) => <span key={hazard}><AlertTriangle size={12} />{hazard}</span>)}</div></div><div className="mission-actions"><button className="outline-action" disabled={saving} onClick={() => onMissionStatus(mission.id, "Accepted")}>Accept mission</button><button className="outline-action" disabled={saving} onClick={() => { const reason = window.prompt("Enter a reason for rejecting this mission") || "Pilot declined"; onMissionStatus(mission.id, "Rejected", reason) }}>Reject with reason</button><button className="primary-action" disabled={saving || mission.status === "In flight"} onClick={() => onMissionStatus(mission.id, "In flight")}>Start survey</button><button className="outline-action" disabled={saving} onClick={() => onMissionStatus(mission.id, "Paused")}>Pause mission</button><button className="outline-action" disabled={saving} onClick={() => onMissionStatus(mission.id, "Completed")}>Mark survey complete</button></div><div className="detail-section finding-section"><div className="section-label">UPLOAD SURVEY FINDINGS <span>RAW FIELD DATA</span></div><p className="empty-inline">Demo mode shows the upload workflow only. Real files are sent via the backend when configured.</p><div className="finding-fields"><label>Observation classification<select value={classification} onChange={(event) => setClassification(event.target.value)}><option>Confirmed observation</option><option>Possible observation</option><option>Unable to verify</option></select></label><label>Observation / pilot note<textarea placeholder="Describe what was observed, including uncertainty." value={finding} onChange={(event) => setFinding(event.target.value)} /></label><label className="upload-drop"><FileText size={17} /><span>Choose photos, video, or field evidence</span><input type="file" multiple accept="image/*,video/*,audio/*" aria-label="Upload survey evidence" /></label><button className="outline-action" onClick={async () => { if (!finding.trim()) { setUploadMessage("Add a brief field observation before submitting."); return } if (!isDemoMode()) { await api.submitFindings(mission.id, { classification, description: finding, submittedAt: new Date().toISOString() }).catch(() => { setUploadMessage("Could not submit findings. Check the network and retry.") }); return } setUploadMessage("Demo finding recorded locally for this session · simulated only"); setFinding("") }}>Submit field observation</button>{uploadMessage ? <span className="inline-feedback" role="status">{uploadMessage}</span> : null}</div></div><div className="no-control-note"><Shield size={14} /><span>Flight controls are intentionally not included. Pilots use their separately authorized flight-control system.</span></div></section>
}

function IntelligencePage({ data, onIncident }: { data: DashboardData; onIncident: (id: string) => void }) {
  const incident = data.incidents[0]
  return <><div className="advisory-banner"><AlertTriangle size={17} /><div><strong>AI-generated analysis is advisory only</strong><span>Qualified responders must review and approve all interpretations before operational use.</span></div></div><div className="intelligence-tabs"><span className="intelligence-tab-active">Raw field data</span><span>AI-generated analysis</span><span className="intelligence-source-count">{data.incidents.reduce((count, item) => count + item.linkedReports.length, 0)} SOURCE ITEMS</span></div><div className="intelligence-grid"><section className="panel raw-data-panel"><PanelTitle title="Raw field data" detail="Original citizen and pilot submissions · source and time retained" />{data.incidents.flatMap((item) => item.linkedReports.map((report) => ({ incident: item, report }))).map(({ incident: parent, report }) => <article className="raw-item" key={report.id}><div className="raw-item-source"><span className="raw-source-icon"><MessageSquareText size={14} /></span><div><strong>Citizen report · {report.id}</strong><span>{parent.id} · {report.address}</span></div><time>{formatDate(report.submittedAt)}</time></div><p>{report.description}</p><div className="raw-item-footer"><span><MapPin size={12} />{report.location.latitude.toFixed(5)}, {report.location.longitude.toFixed(5)} · source: simulated</span><StatusTag label={report.status} tone={report.status} /></div></article>)}{data.missions.flatMap((mission) => mission.observations.map((observation) => ({ mission, observation }))).map(({ mission, observation }) => <article className="raw-item" key={observation.id}><div className="raw-item-source"><span className="raw-source-icon raw-drone"><Crosshair size={14} /></span><div><strong>Pilot observation · {observation.id}</strong><span>{mission.id} · {observation.source}</span></div><time>{formatDate(observation.observedAt)}</time></div><p>{observation.description}</p><div className="raw-item-footer"><span><MapPin size={12} />{observation.location.latitude.toFixed(5)}, {observation.location.longitude.toFixed(5)} · {observation.classification}</span></div></article>)}</section><section className="panel ai-analysis-panel"><div className="analysis-header"><span className="analysis-icon"><Zap size={15} /></span><div><span>ADVISORY ANALYSIS</span><h2>{incident.title}</h2></div><button className="quiet-button" onClick={() => window.print()}><FileText size={14} />Export / Print PDF</button></div><div className="analysis-confidence"><div><span>Model confidence</span><strong>{Math.round(incident.confidence * 100)}%</strong></div><div className="confidence-track"><span style={{ width: `${incident.confidence * 100}%` }} /></div><span>Confidence is not a verified finding or dispatch decision.</span></div><AnalysisSection title="Incident summary" text={incident.summary} references={incident.linkedReports.slice(0, 2).map((report) => report.id)} /><AnalysisSection title="Potential affected locations" text={`${incident.area}; individual source locations are shown separately on the incident map.`} references={incident.linkedReports.map((report) => report.id)} /><AnalysisSection title="Possible people affected" text={`${incident.peopleAffected ?? "Unknown"} reported affected · ${incident.peopleTrapped ?? "Unknown"} possibly trapped. Citizen estimates are unverified; no AI detection is confirmation of a person's presence.`} references={incident.linkedReports.filter((report) => report.peopleAffected || report.peopleTrapped).map((report) => report.id)} /><AnalysisSection title="Potential hazards" text={incident.hazards.join(" · ")} references={incident.linkedReports.map((report) => report.id)} /><AnalysisSection title="Recommended review priorities" text="Confirm safe access points, validate any person-sighting claim with qualified responders, and request a ground assessment when safe. Recommendations are not an operational order." references={incident.linkedReports.slice(0, 2).map((report) => report.id)} /><AnalysisSection title="Uncertainties & missing information" text="Building occupancy, structural stability, exact smoke extent, and the possible north-entrance sighting have not been verified by the prototype data." references={incident.linkedReports.slice(0, 1).map((report) => report.id)} /><button className="text-button view-source-button" onClick={() => onIncident(incident.id)}>Review linked source reports <ChevronRight size={14} /></button></section></div></>
}

function AnalysisSection({ title, text, references }: { title: string; text: string; references: string[] }) {
  return <section className="analysis-section"><div className="analysis-section-title">{title}</div><p>{text}</p><div className="analysis-references">Source references: {references.length ? references.map((reference) => <span key={reference}>{reference}</span>) : "No linked source items"}</div></section>
}
