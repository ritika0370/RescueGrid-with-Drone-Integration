"use client"

import { useEffect } from "react"
import { MapContainer, Marker, TileLayer, useMapEvents } from "react-leaflet"
import type { LatLng } from "leaflet"

function ClickToSet({ onPick, disabled }: { onPick: (latitude: number, longitude: number) => void; disabled: boolean }) {
  useMapEvents({ click(event) { if (!disabled) onPick(event.latlng.lat, event.latlng.lng) } })
  return null
}

export function LocationPickerMap({ value, onChange, readOnly = false }: { value: { latitude: number; longitude: number } | null; onChange: (point: { latitude: number; longitude: number }) => void; readOnly?: boolean }) {
  return <MapContainer center={value ? [value.latitude, value.longitude] : [20, 0]} zoom={value ? 14 : 2} scrollWheelZoom className="citizen-map" aria-label={readOnly ? "Original emergency report location map" : "Choose or adjust emergency report location on map"}>
    <TileLayer attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>' url={process.env.NEXT_PUBLIC_MAP_TILE_URL || "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"} />
    {!readOnly ? <ClickToSet onPick={(latitude, longitude) => onChange({ latitude, longitude })} disabled={readOnly} /> : null}
    {value ? <Marker position={[value.latitude, value.longitude]} draggable={!readOnly} eventHandlers={readOnly ? undefined : { dragend(event) { const point = (event.target as { getLatLng: () => LatLng }).getLatLng(); onChange({ latitude: point.lat, longitude: point.lng }) } }} /> : null}
  </MapContainer>
}
