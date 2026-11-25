"use client"

import dynamic from "next/dynamic"
import { useEffect, useState } from "react"
import { Activity, ArrowLeft, ArrowRight, AudioLines, Camera, Check, ChevronRight, Clock3, Crosshair, FileText, Flame, HeartPulse, ImagePlus, MapPin, Mic, PhoneCall, ShieldAlert, Siren, Waves } from "lucide-react"
import { api, isDemoMode } from "@/lib/api"
import { createDemoReport } from "@/lib/demo-service"
import { BRAND } from "@/shared/design-system"
import { EMERGENCY_CATEGORIES, type CitizenReport, type Coordinates } from "@/shared/types"

const LocationPickerMap = dynamic(() => import("./location-picker-map").then((module) => module.LocationPickerMap), { ssr: false, loading: () => <div className="citizen-map map-loading">Loading map…</div> })
const recentDemoReports: CitizenReport[] = []
const categoryGlyphs = [Flame, Waves, Activity, AlertTriangleIcon, CarAccidentIcon, HeartPulse, UsersIcon, Siren]

function AlertTriangleIcon(props: React.ComponentProps<typeof Siren>) { return <ShieldAlert {...props} /> }
function CarAccidentIcon(props: React.ComponentProps<typeof Siren>) { return <Crosshair {...props} /> }
function UsersIcon(props: React.ComponentProps<typeof Siren>) { return <Activity {...props} /> }

type CitizenAppProps = { emergencyPhone?: string }

export function CitizenApp({ emergencyPhone }: CitizenAppProps) {
  const availablePhone = emergencyPhone && /^\+[1-9]\d{7,14}$/.test(emergencyPhone) ? emergencyPhone : undefined
  const [screen, setScreen] = useState<"home" | "report" | "confirmation" | "reports" | "report-detail" | "safety">("home")
  const [category, setCategory] = useState<CitizenReport["category"]>(EMERGENCY_CATEGORIES[0])
  const [location, setLocation] = useState<Coordinates | null>(null)
  const [locationLabel, setLocationLabel] = useState("")
  const [address, setAddress] = useState("")
  const [description, setDescription] = useState("")
  const [affected, setAffected] = useState("")
  const [trapped, setTrapped] = useState("")
  const [danger, setDanger] = useState<"yes" | "no" | "unknown">("unknown")
  const [media, setMedia] = useState<File[]>([])
  const [reports, setReports] = useState<CitizenReport[]>(recentDemoReports)
  const [createdReport, setCreatedReport] = useState<CitizenReport | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState("")
  const [uploadProgress, setUploadProgress] = useState("")
  const [reportList, setReportList] = useState<CitizenReport[]>([])
  const [reportsLoading, setReportsLoading] = useState(false)
  const [locationBusy, setLocationBusy] = useState(false)
  const [detailLoading, setDetailLoading] = useState(false)
  const [detailUpdates, setDetailUpdates] = useState<Array<{ at: string; text: string }>>([])
  const [detailNote, setDetailNote] = useState("")
  const [detailMedia, setDetailMedia] = useState<File[]>([])
  const [updateBusy, setUpdateBusy] = useState(false)

  useEffect(() => { if (screen === "reports" && !isDemoMode()) { setReportsLoading(true); api.myReports().then(setReportList).catch(() => setError("Report history could not be loaded. Check your network connection.")).finally(() => setReportsLoading(false)) } }, [screen])

  function openReport(nextCategory = category) {
    setCategory(nextCategory)
    setCreatedReport(null)
    setError("")
    setScreen("report")
  }

  async function openReportDetail(report: CitizenReport) {
    setCreatedReport(report)
    setDetailNote("")
    setDetailMedia([])
    setError("")
    setScreen("report-detail")
    setDetailLoading(true)
    if (isDemoMode()) {
      setDetailUpdates([{ at: report.submittedAt, text: `Original report submitted · ${report.status}` }])
      setDetailLoading(false)
      return
    }
    try {
      const [detail, status] = await Promise.all([api.report(report.id), api.reportStatus(report.id)])
      setCreatedReport(detail)
      setDetailUpdates(status.updates || [])
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Report details could not be loaded.")
    } finally { setDetailLoading(false) }
  }

  async function submitFollowUp(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!createdReport || (!detailNote.trim() && detailMedia.length === 0)) return
    setUpdateBusy(true)
    setError("")
    try {
      if (!isDemoMode()) {
        if (detailNote.trim()) await api.addReportUpdate(createdReport.id, { text: detailNote.trim() })
        for (const file of detailMedia) {
          const form = new FormData()
          form.append("file", file)
          await api.uploadReportMedia(createdReport.id, form)
        }
        const [detail, status] = await Promise.all([api.report(createdReport.id), api.reportStatus(createdReport.id)])
        setCreatedReport(detail)
        setDetailUpdates(status.updates || [])
      } else {
        const newMedia = detailMedia.map((file) => ({ id: `DEMO-MEDIA-${crypto.randomUUID()}`, type: file.type.startsWith("audio/") ? "audio" as const : file.type.startsWith("video/") ? "video" as const : "image" as const, url: URL.createObjectURL(file), label: file.name }))
        const updated = { ...createdReport, media: [...createdReport.media, ...newMedia] }
        setCreatedReport(updated)
        setReports((current) => current.map((report) => report.id === updated.id ? updated : report))
        setReportList((current) => current.map((report) => report.id === updated.id ? updated : report))
        setDetailUpdates((current) => [...current, { at: new Date().toISOString(), text: detailNote.trim() || `${detailMedia.length} media item${detailMedia.length === 1 ? "" : "s"} attached` }])
      }
      setDetailNote("")
      setDetailMedia([])
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Update could not be submitted. The original report is unchanged.")
    } finally { setUpdateBusy(false) }
  }

  async function useGPS() {
    setLocationBusy(true)
    setError("")
    if (!navigator.geolocation) { setError("Location is unavailable in this browser. Choose a point on the map or enter coordinates."); setLocationBusy(false); return }
    navigator.geolocation.getCurrentPosition((position) => {
      const point = { latitude: position.coords.latitude, longitude: position.coords.longitude, accuracyMeters: position.coords.accuracy, source: "gps" as const }
      setLocation(point)
      setLocationLabel(`GPS · ±${Math.round(position.coords.accuracy)} m`)
      setLocationBusy(false)
    }, () => { setError("GPS permission or signal unavailable. Choose a point on the map or enter coordinates manually."); setLocationBusy(false) }, { enableHighAccuracy: true, timeout: 12000, maximumAge: 30000 })
  }

  function pickManualPoint(point: { latitude: number; longitude: number }) {
    setLocation({ ...point, source: "manual" })
    setLocationLabel("Manually placed on map")
  }

  function setCoordinate(index: 0 | 1, value: string) {
    const number = Number(value)
    if (!value.trim() || !Number.isFinite(number)) { setLocation(null); setLocationLabel("Manual coordinate required"); return }
    const current = location?.source === "manual" ? location : { latitude: 0, longitude: 0, source: "manual" as const }
    const updated = index === 0 ? { ...current, latitude: number } : { ...current, longitude: number }
    if (updated.latitude < -90 || updated.latitude > 90 || updated.longitude < -180 || updated.longitude > 180) { setError("Enter a valid latitude (−90 to 90) and longitude (−180 to 180)."); return }
    setError("")
    setLocation(updated)
    setLocationLabel("Manually entered coordinates")
  }

  async function submitReport(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!location) { setError("Add your location with GPS, map, or coordinates. Emergency category and location are required."); return }
    setBusy(true)
    setError("")
    try {
      const payload = { category, description: description.trim(), address: address.trim() || locationLabel || "Location set on map", location, peopleAffected: Number(affected) || undefined, peopleTrapped: Number(trapped) || undefined, personallyInDanger: danger === "unknown" ? undefined : danger === "yes" }
      const created = isDemoMode() ? await createDemoReport(payload) : await api.createReport(payload)
      const submitted = created as CitizenReport
      setCreatedReport(submitted)
      setReports((current) => [submitted, ...current])
      setScreen("confirmation")
      if (!isDemoMode() && media.length) {
        setUploadProgress(`Uploading 0 of ${media.length} attachments…`)
        try {
          for (const [index, file] of media.entries()) {
            const form = new FormData()
            form.append("file", file)
            await api.uploadReportMedia(created.id, form)
            setUploadProgress(`Uploading ${index + 1} of ${media.length} attachments…`)
          }
        } catch {
          setError("The report was submitted, but an attachment could not be uploaded. Add it again from report details when connected.")
        }
      }
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not submit report. Check your connection and try again.")
    } finally { setBusy(false); setUploadProgress("") }
  }

  const visibleReports = isDemoMode() ? reports : reportList

  return <div className="citizen-root"><div className="citizen-device"><header className="citizen-top"><a className="citizen-brand" href="/citizen" aria-label="CIRRUS citizen home"><span className="citizen-brand-mark">C</span><span><strong>CIRRUS</strong><small>RESPONSE COORDINATION</small></span></a><span className="citizen-prototype">PROTOTYPE</span></header>
    {screen === "home" ? <main className="citizen-home"><div className="citizen-home-copy"><span className="citizen-eyebrow">CITIZEN REPORTING</span><h1>Help starts<br />with a report.</h1><p>A simple way to share what is happening and where help is needed.</p></div><button className="citizen-sos" onClick={() => openReport()}><span>SOS</span><small>Tap to report an emergency</small></button><div className="citizen-location-card"><span className="citizen-location-icon"><MapPin size={16} /></span><div><strong>Your location</strong><small>{locationLabel || "Not shared yet · optional"}</small></div><button onClick={() => { void useGPS() }} disabled={locationBusy}>{locationBusy ? "Locating…" : "Use GPS"}</button></div><section className="citizen-call-card" aria-labelledby="citizen-call-title"><div className="call-card-index">VOICE CHANNEL · 02</div><div className="call-card-copy"><h2 id="citizen-call-title">Prefer to speak with someone?</h2><p>{availablePhone ? "Call the configured response desk. This line does not replace local emergency services." : "Phone reporting is not configured yet. Use SOS to send a location-based report."}</p></div>{availablePhone ? <a className="citizen-call-action" href={`tel:${availablePhone}`}><PhoneCall aria-hidden="true" /><span>Call the response desk</span><strong>{availablePhone}</strong></a> : <div className="citizen-call-unavailable" role="status"><strong>PHONE LINE NOT CONFIGURED</strong><span>Online SOS is available</span></div>}</section><section className="citizen-category-section"><div className="citizen-section-heading"><strong>Choose a category</strong><span>You can change this later</span></div><div className="citizen-category-grid">{EMERGENCY_CATEGORIES.map((item, index) => { const Icon = categoryGlyphs[index]; return <button key={item} onClick={() => openReport(item)}><span className="citizen-category-icon"><Icon size={15} /></span><span>{item}</span></button> })}</div></section><section className="citizen-recent"><div className="citizen-section-heading"><strong>Recent reports</strong><button onClick={() => setScreen("reports")}>View all</button></div>{reports.length ? reports.slice(0, 2).map((report) => <button key={report.id} className="citizen-recent-item" onClick={() => { void openReportDetail(report) }}><span><strong>{report.category}</strong><small>{report.id} · {new Date(report.submittedAt).toLocaleString()}</small></span><StatusPill status={report.status} /><ChevronRight size={15} /></button>) : <div className="citizen-empty"><strong>No reports yet</strong><span>Your submitted reports will appear here.</span></div>}</section><div className="citizen-footer-links"><button onClick={() => setScreen("safety")}>Safety information</button><a href="/login">Sign in / create account</a></div><p className="citizen-disclaimer">This prototype does not replace official emergency phone services. No local number is configured.</p></main> : null}

    {screen === "report" ? <main className="citizen-report"><button className="back-link" onClick={() => setScreen("home")}><ArrowLeft size={15} />Back to home</button><div className="citizen-report-heading"><span className="citizen-eyebrow">QUICK SOS · GUEST REPORTING</span><h1>What is happening?</h1><p>Share what you can. A category and location are enough to send an SOS.</p></div><form onSubmit={submitReport}><label className="citizen-field-label">EMERGENCY CATEGORY</label><div className="report-category-scroll">{EMERGENCY_CATEGORIES.map((item) => <button type="button" key={item} className={`report-category-chip ${category === item ? "chip-chosen" : ""}`} onClick={() => setCategory(item)}>{item}</button>)}</div><div className="citizen-field-heading"><label className="citizen-field-label" htmlFor="citizen-address">YOUR LOCATION</label><button type="button" className="text-button" onClick={() => void useGPS()} disabled={locationBusy}><Crosshair size={13} />{locationBusy ? "Locating…" : "Use GPS"}</button></div><input id="citizen-address" className="citizen-input" placeholder="Address or nearby landmark (optional)" value={address} onChange={(event) => setAddress(event.target.value)} /><div className="citizen-map-shell"><LocationPickerMap value={location} onChange={pickManualPoint} /></div><div className="location-confirmation"><MapPin size={13} /><span>{location ? `${locationLabel} · ${location.latitude.toFixed(5)}, ${location.longitude.toFixed(5)}` : "Tap the map to select a location, or use GPS."}</span><span className="location-accuracy">{location?.accuracyMeters ? `±${Math.round(location.accuracyMeters)} m` : ""}</span></div><div className="coordinate-fields"><label>Latitude<input className="citizen-input" inputMode="decimal" placeholder="e.g. 40.7128" value={location?.source === "manual" && location.latitude !== 0 ? String(location.latitude) : ""} onChange={(event) => setCoordinate(0, event.target.value)} /></label><label>Longitude<input className="citizen-input" inputMode="decimal" placeholder="e.g. −74.0060" value={location?.source === "manual" && location.longitude !== 0 ? String(location.longitude) : ""} onChange={(event) => setCoordinate(1, event.target.value)} /></label></div><label className="citizen-field-label" htmlFor="citizen-description">SHORT DESCRIPTION · OPTIONAL</label><textarea id="citizen-description" className="citizen-input citizen-textarea" placeholder="What can responders see or hear?" maxLength={500} value={description} onChange={(event) => setDescription(event.target.value)} /><div className="citizen-count">{description.length}/500</div><label className="citizen-field-label">PEOPLE AFFECTED · IF KNOWN</label><div className="citizen-number-fields"><input className="citizen-input" inputMode="numeric" aria-label="People affected" placeholder="Affected" value={affected} onChange={(event) => setAffected(event.target.value)} /><input className="citizen-input" inputMode="numeric" aria-label="People trapped or injured" placeholder="Trapped or injured" value={trapped} onChange={(event) => setTrapped(event.target.value)} /></div><label className="citizen-field-label">ARE YOU PERSONALLY IN DANGER?</label><div className="danger-choices">{([["yes", "Yes"], ["no", "No"], ["unknown", "Unsure"]] as const).map(([value, label]) => <button type="button" key={value} className={danger === value ? "danger-chosen" : ""} onClick={() => setDanger(value)}>{label}</button>)}</div><label className="citizen-field-label">ADD MEDIA · OPTIONAL</label><div className="citizen-media-actions"><label className="media-action"><Camera size={16} /><span>Take photo</span><input type="file" accept="image/*" capture="environment" onChange={(event) => setMedia((current) => [...current, ...Array.from(event.target.files ?? [])])} /></label><label className="media-action"><ImagePlus size={16} /><span>Image / video</span><input type="file" accept="image/*,video/*" multiple onChange={(event) => setMedia((current) => [...current, ...Array.from(event.target.files ?? [])])} /></label><label className="media-action"><Mic size={16} /><span>Audio note</span><input type="file" accept="audio/*" onChange={(event) => setMedia((current) => [...current, ...Array.from(event.target.files ?? [])])} /></label></div><span className="media-hint">{media.length ? `${media.length} attachment${media.length === 1 ? "" : "s"} ready` : "Photos, audio, and video are optional. No permission is needed until you choose media."}</span>{uploadProgress ? <div className="upload-progress" role="status"><span />{uploadProgress}</div> : null}{error ? <div className="citizen-error" role="alert">{error}</div> : null}<button type="submit" className="submit-sos" disabled={busy}><Siren size={17} />{busy ? "Submitting report…" : "Submit SOS report"}</button><p className="citizen-submit-note">Only category and location are required. Submission does not confirm dispatch.</p></form></main> : null}

    {screen === "confirmation" ? <main className="citizen-confirm"><div className="confirm-check"><Check size={24} /></div><span className="citizen-eyebrow">REPORT RECEIVED</span><h1>Your report is in the queue.</h1><p>The status below is from this prototype. No rescue dispatch is confirmed.</p><div className="confirmation-card"><span>REPORT ID</span><strong>{createdReport?.id}</strong><span>SUBMITTED</span><strong>{createdReport?.submittedAt ? new Date(createdReport.submittedAt).toLocaleString() : "Just now"}</strong><span>STATUS</span><StatusPill status={createdReport?.status || "Submitted"} /></div><div className="confirm-actions"><button className="submit-sos" onClick={() => setScreen("reports")}>View my reports <ArrowRight size={15} /></button><button className="secondary-action" onClick={() => { setDescription(""); setLocation(null); setAddress(""); setScreen("home") }}>Back to home</button></div>{uploadProgress ? <p className="upload-progress" role="status">{uploadProgress}</p> : null}{error ? <div className="citizen-error" role="alert">{error}</div> : null}<button className="add-update-link" onClick={() => createdReport ? void openReportDetail(createdReport) : setScreen("reports")}>Add further information</button></main> : null}

    {screen === "report-detail" && createdReport ? <main className="citizen-report"><button className="back-link" onClick={() => setScreen("reports")}><ArrowLeft size={15} />Back to my reports</button><div className="citizen-report-heading"><span className="citizen-eyebrow">ORIGINAL REPORT · {createdReport.id}</span><h1>{createdReport.category}</h1><p>Additional updates are stored separately. Your original report stays unchanged.</p></div><div className="report-detail-summary"><div><span>CURRENT STATUS</span><StatusPill status={createdReport.status} /></div><div><span>SUBMITTED</span><strong>{new Date(createdReport.submittedAt).toLocaleString()}</strong></div><div><span>LOCATION SOURCE</span><strong>{createdReport.location.source === "manual" ? "Manually selected" : "GPS location"}</strong></div></div><section className="report-detail-section"><h2>Original information</h2><p>{createdReport.description || "No text description was included."}</p><strong>{createdReport.address}</strong><div className="report-detail-facts"><span>{createdReport.peopleAffected === undefined ? "People affected not provided" : `${createdReport.peopleAffected} people affected`}</span><span>{createdReport.peopleTrapped === undefined ? "People trapped or injured not provided" : `${createdReport.peopleTrapped} trapped or injured`}</span><span>{createdReport.personallyInDanger === undefined ? "Personal danger unknown" : createdReport.personallyInDanger ? "Reporter indicated personal danger" : "Reporter indicated no personal danger"}</span></div></section><section className="report-detail-section"><h2>Original location</h2><p>{createdReport.location.source === "manual" ? "Manually entered or selected · original point preserved" : "GPS location · original point preserved"}</p><div className="citizen-map-shell"><LocationPickerMap value={createdReport.location} onChange={() => undefined} readOnly /></div><small>{createdReport.location.latitude.toFixed(5)}, {createdReport.location.longitude.toFixed(5)}{createdReport.location.accuracyMeters ? ` · ±${Math.round(createdReport.location.accuracyMeters)} m` : ""}</small></section><section className="report-detail-section"><h2>Submitted media</h2>{createdReport.media.length ? <div className="report-media-grid">{createdReport.media.map((item) => <article className="report-media-item" key={item.id}>{item.type === "image" ? <img src={item.url} alt={item.label || "Photo attached to the report"} /> : item.type === "video" ? <video src={item.url} controls aria-label={item.label || "Video attached to the report"} /> : <audio src={item.url} controls aria-label={item.label || "Audio attached to the report"} />}<span>{item.label || item.type}</span></article>)}</div> : <p>No media attached to the original report.</p>}</section><section className="report-detail-section"><h2>Status and update history</h2>{detailLoading ? <p>Loading report updates…</p> : detailUpdates.length ? <ol className="report-update-list">{detailUpdates.map((update, index) => <li key={`${update.at}-${index}`}><time>{new Date(update.at).toLocaleString()}</time><p>{update.text}</p></li>)}</ol> : <p>No status updates have been returned yet.</p>}</section><form className="report-follow-up" onSubmit={submitFollowUp}><h2>Add information</h2><p>Text and media are optional. Your update will not replace the original report.</p><label htmlFor="report-follow-up-text">Additional note</label><textarea id="report-follow-up-text" value={detailNote} onChange={(event) => setDetailNote(event.target.value)} rows={3} maxLength={500} placeholder="Share a new observation or correction" /><label className="report-follow-up-upload">Add photo, audio, or video<input type="file" accept="image/*,audio/*,video/*" multiple onChange={(event) => setDetailMedia(Array.from(event.target.files || []))} /></label>{detailMedia.length ? <small>{detailMedia.length} file{detailMedia.length === 1 ? "" : "s"} selected</small> : null}{error ? <div className="citizen-error" role="alert">{error}</div> : null}<button className="submit-sos" type="submit" disabled={updateBusy || (!detailNote.trim() && detailMedia.length === 0)}>{updateBusy ? "Sending update…" : "Send update"}</button></form></main> : null}

    {screen === "reports" ? <main className="citizen-report"><button className="back-link" onClick={() => setScreen("home")}><ArrowLeft size={15} />Back to home</button><div className="citizen-report-heading"><span className="citizen-eyebrow">REPORT HISTORY</span><h1>My reports</h1><p>Original reports are preserved. Backend status updates appear here when connected.</p></div>{reportsLoading ? <div className="citizen-empty"><span className="loading-dot" />Loading reports…</div> : null}{!reportsLoading && visibleReports.length === 0 ? <div className="citizen-empty"><strong>No reports to show</strong><span>Submitted reports appear here. Demo mode keeps reports in this session only.</span></div> : null}{visibleReports.map((report) => <button key={report.id} className="history-report" onClick={() => { void openReportDetail(report) }}><div><strong>{report.id}</strong><span>{report.category} · {report.address || "Location provided"}</span><small>{new Date(report.submittedAt).toLocaleString()}</small></div><StatusPill status={report.status} /><ChevronRight size={15} /></button>)}{error ? <div className="citizen-error" role="alert">{error}</div> : null}</main> : null}

    {screen === "safety" ? <main className="citizen-report"><button className="back-link" onClick={() => setScreen("home")}><ArrowLeft size={15} />Back to home</button><div className="citizen-report-heading"><span className="citizen-eyebrow">SAFETY INFORMATION</span><h1>Keep yourself safe.</h1></div><div className="safety-warning"><ShieldAlert size={18} /><div><strong>This app does not replace emergency services.</strong><span>{availablePhone ? <>Call the response desk at <a href={`tel:${availablePhone}`}>{availablePhone}</a>. This app does not replace verified local emergency services.</> : "Phone reporting is not configured. Contact verified local emergency services if you are in immediate danger."}</span></div></div>{[["Move away from immediate danger", "If safe, move to a clear area and follow qualified responder instructions."], ["Do not enter hazards", "Avoid damaged buildings, floodwater, fire areas, and restricted zones."], ["Share only what you know", "Mark uncertain reports as possible. Do not approach hazards to gather information."], ["Your location", "Use GPS, tap the map, or enter coordinates. A manually selected point is clearly labeled."]].map(([title, text], index) => <article className="safety-tip" key={title}><b>{String(index + 1).padStart(2, "0")}</b><span><strong>{title}</strong><small>{text}</small></span></article>)}</main> : null}
  </div><aside className="citizen-info-rail"><a className="back-dashboard" href="/">← Operations dashboard</a><div className="rail-copy"><span className="citizen-eyebrow">CITIZEN COMPANION</span><h2>One clear path from SOS to coordinated response.</h2><p>Fast guest reporting on the left. Source-preserving department review and manual pilot survey workflow in the dashboard.</p></div><div className="rail-steps"><div><i>01</i><span><strong>Report</strong><small>Location + category is enough.</small></span></div><div><i>02</i><span><strong>Review</strong><small>Reports stay individually attributable.</small></span></div><div><i>03</i><span><strong>Coordinate</strong><small>Manual survey workflow; no flight control.</small></span></div></div><div className="rail-disclaimer"><ShieldAlert size={15} /><span>Prototype only · Demo information is simulated and does not represent a real incident or dispatch.</span></div></aside></div>
}

function StatusPill({ status }: { status: string }) {
  return <span className={`citizen-status status-${status.toLowerCase().replaceAll(" ", "-")}`}><i />{status}</span>
}
