"use client"

import { useEffect, useMemo } from "react"
import { CircleMarker, MapContainer, Polygon, TileLayer, Tooltip, useMap } from "react-leaflet"
import type { Coordinates, Drone, DroneStation, Incident, Mission, ResponseDepartment } from "@/shared/types"

const colorByCategory: Record<string, string> = {
  Fire: "#dc4b4e", Flood: "#348eaf", Earthquake: "#9868b4", "Building collapse": "#dc8c36",
  "Road accident": "#557dba", "Medical emergency": "#358b6d", "Missing or trapped person": "#bd6383", "Other emergency": "#66747f",
}
const tileUrl = process.env.NEXT_PUBLIC_MAP_TILE_URL || "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"

function FitBounds({ points }: { points: Coordinates[] }) {
  const map = useMap()
  const signature = points.map(({ latitude, longitude }) => `${latitude},${longitude}`).join("|")
  useEffect(() => {
    if (points.length > 1) map.fitBounds(points.map(({ latitude, longitude }) => [latitude, longitude]), { padding: [34, 34], maxZoom: 14 })
    else if (points.length === 1) map.setView([points[0].latitude, points[0].longitude], 13)
  // The coordinate signature avoids resetting map zoom for identical point arrays recreated during rerenders.
  }, [map, signature])
  return null
}

export function IncidentMap({ incidents, drones, missions, selectedId, onSelect, departments = [], droneStations = [], unlinkedReports = [] }: {
  incidents: Incident[]
  drones: Drone[]
  missions: Mission[]
  selectedId?: string
  onSelect?: (id: string) => void
  departments?: ResponseDepartment[]
  droneStations?: DroneStation[]
  unlinkedReports?: Incident["linkedReports"]
}) {
  const visibleIncidents = useMemo(() => incidents.filter((incident) => incident.status !== "Resolved" && incident.status !== "Closed"), [incidents])
  const mission = missions.find((item) => item.incidentId === selectedId) ?? missions[0]
  const visibleReports = [...visibleIncidents.flatMap((incident) => incident.linkedReports), ...unlinkedReports]
  const positionedDrones = drones.filter((drone) => drone.status !== "Offline")
  const allPoints = useMemo(() => [
    ...visibleIncidents.map((incident) => incident.location),
    ...visibleReports.map((report) => report.location),
    ...positionedDrones.map((drone) => drone.location),
    ...departments.map((department) => department.location),
    ...droneStations.map((station) => station.location),
    ...(mission?.boundary || []),
  ], [visibleIncidents, visibleReports, positionedDrones, departments, droneStations, mission])
  const firstPoint = allPoints[0]
  const center: [number, number] = firstPoint ? [firstPoint.latitude, firstPoint.longitude] : [20, 0]
  const mapIsSimulated = incidents.some((incident) => incident.location.source === "simulated") || drones.some((drone) => drone.simulated)

  return (
    <MapContainer center={center} zoom={firstPoint ? 12 : 2} scrollWheelZoom className="ops-map" aria-label={mapIsSimulated ? "Simulated incident, report, department and drone map" : "Incident, report, department and drone map"}>
      <TileLayer attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>' url={tileUrl} />
      <FitBounds points={allPoints} />
      {visibleIncidents.map((incident) => (
        <CircleMarker key={incident.id} center={[incident.location.latitude, incident.location.longitude]} radius={selectedId === incident.id ? 12 : 9}
          pathOptions={{ color: "#fff", weight: 2, fillColor: colorByCategory[incident.category] || "#66747f", fillOpacity: 0.96 }}
          eventHandlers={{ click: () => onSelect?.(incident.id) }}>
          <Tooltip direction="top" offset={[0, -10]}><strong>{incident.id}</strong><br />{incident.category} · {incident.priority} · {incident.status}</Tooltip>
        </CircleMarker>
      ))}
      {visibleReports.map((report) => <CircleMarker key={report.id} center={[report.location.latitude, report.location.longitude]} radius={4}
        pathOptions={{ color: "#fff", weight: 1, fillColor: "#52667a", fillOpacity: 0.9 }}><Tooltip>{report.id} · individual source location</Tooltip></CircleMarker>)}
      {departments.map((department) => <CircleMarker key={department.id} center={[department.location.latitude, department.location.longitude]} radius={8}
        pathOptions={{ color: "#fff", weight: 2, fillColor: "#6c7b8b", fillOpacity: 1 }}><Tooltip>{department.name} · department</Tooltip></CircleMarker>)}
      {droneStations.map((station) => <CircleMarker key={station.id} center={[station.location.latitude, station.location.longitude]} radius={8}
        pathOptions={{ color: "#fff", weight: 2, fillColor: "#378b82", fillOpacity: 1 }}><Tooltip>{station.name} · station · {station.availableDrones ?? "—"} available</Tooltip></CircleMarker>)}
      {positionedDrones.map((drone) => <CircleMarker key={drone.id} center={[drone.location.latitude, drone.location.longitude]} radius={7}
        pathOptions={{ color: "#fff", weight: 2, fillColor: "#43a7bd", fillOpacity: 1 }}><Tooltip>{drone.id} · {drone.status}{drone.simulated ? " · simulated position" : " · backend telemetry"}</Tooltip></CircleMarker>)}
      {mission?.boundary.length ? <Polygon positions={mission.boundary.map(({ latitude, longitude }) => [latitude, longitude])} pathOptions={{ color: "#db9c42", weight: 2, fillOpacity: 0.08, dashArray: "5 5" }} /> : null}
    </MapContainer>
  )
}
