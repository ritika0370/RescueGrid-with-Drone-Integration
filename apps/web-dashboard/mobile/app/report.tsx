import { router, useLocalSearchParams } from "expo-router"
import * as ImagePicker from "expo-image-picker"
import * as Location from "expo-location"
import { AudioModule, RecordingPresets, useAudioRecorder, useAudioRecorderState } from "expo-audio"
import { useState } from "react"
import { Alert, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from "react-native"
import { SafeAreaView } from "react-native-safe-area-context"
import { EMERGENCY_CATEGORIES } from "../../shared/types"
import { BRAND } from "../../shared/design-system"
import { createReport, uploadReportMedia } from "../src/api"

export default function ReportScreen() {
  const params = useLocalSearchParams<{ category?: string; location?: string; latitude?: string; longitude?: string; accuracyMeters?: string }>()
  const initialLatitude = Number(params.latitude)
  const initialLongitude = Number(params.longitude)
  const hasInitialGps = Boolean(params.latitude && params.longitude && Number.isFinite(initialLatitude) && Number.isFinite(initialLongitude))
  const [category, setCategory] = useState<string>(params.category || "Other emergency")
  const [description, setDescription] = useState("")
  const [address, setAddress] = useState("")
  const [people, setPeople] = useState("")
  const [trapped, setTrapped] = useState("")
  const [inDanger, setInDanger] = useState<boolean | undefined>()
  const [locationText, setLocationText] = useState(params.location || "")
  const [coordinates, setCoordinates] = useState<{ latitude: number; longitude: number; accuracyMeters?: number; source: "gps" | "manual" } | null>(() => hasInitialGps ? { latitude: initialLatitude, longitude: initialLongitude, accuracyMeters: Number(params.accuracyMeters) || undefined, source: "gps" } : null)
  const [manualLatitude, setManualLatitude] = useState("")
  const [manualLongitude, setManualLongitude] = useState("")
  const [attachments, setAttachments] = useState<Array<{ uri: string; name: string; type: string }>>([])
  const [busy, setBusy] = useState(false)
  const [reportId, setReportId] = useState("")
  const [reportStatus, setReportStatus] = useState("Submitted")
  const [submittedAt, setSubmittedAt] = useState("")
  const [mediaProgress, setMediaProgress] = useState("")
  const recorder = useAudioRecorder(RecordingPresets.HIGH_QUALITY)
  const recordingState = useAudioRecorderState(recorder)

  async function locate() {
    try {
      const permission = await Location.requestForegroundPermissionsAsync()
      if (permission.status !== "granted") { Alert.alert("Location permission not granted", "You can enter a landmark or coordinates manually."); return }
      const current = await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.Balanced })
      setCoordinates({ latitude: current.coords.latitude, longitude: current.coords.longitude, accuracyMeters: current.coords.accuracy ?? undefined, source: "gps" })
      setLocationText(`${current.coords.latitude.toFixed(5)}, ${current.coords.longitude.toFixed(5)} · ±${Math.round(current.coords.accuracy ?? 0)} m · GPS`)
    } catch { Alert.alert("Location unavailable", "Enter a nearby landmark or coordinates instead.") }
  }

  async function selectImage(fromCamera: boolean) {
    const permission = fromCamera ? await ImagePicker.requestCameraPermissionsAsync() : await ImagePicker.requestMediaLibraryPermissionsAsync()
    if (!permission.granted) { Alert.alert("Permission needed", "You can still submit a report without media."); return }
    const result = fromCamera
      ? await ImagePicker.launchCameraAsync({ mediaTypes: ["images"], quality: 0.7 })
      : await ImagePicker.launchImageLibraryAsync({ mediaTypes: ["images", "videos"], quality: 0.7 })
    if (!result.canceled) setAttachments((items) => [...items, ...result.assets.map((asset) => ({ uri: asset.uri, name: asset.fileName || `evidence-${items.length + 1}`, type: asset.mimeType || "image/jpeg" }))])
  }

  async function toggleRecording() {
    try {
      if (recordingState.isRecording) {
        await recorder.stop()
        if (recorder.uri) setAttachments((items) => [...items, { uri: recorder.uri!, name: "voice-note.m4a", type: "audio/m4a" }])
      } else {
        const permission = await AudioModule.requestRecordingPermissionsAsync()
        if (!permission.granted) { Alert.alert("Microphone permission not granted", "You can still submit your report without audio."); return }
        await recorder.prepareToRecordAsync()
        recorder.record()
      }
    } catch { Alert.alert("Audio unavailable", "You can still submit your report with text and location.") }
  }

  async function submit() {
    const latitude = Number(manualLatitude)
    const longitude = Number(manualLongitude)
    const hasManualCoordinates = manualLatitude.trim() !== "" && manualLongitude.trim() !== "" && Number.isFinite(latitude) && Number.isFinite(longitude) && latitude >= -90 && latitude <= 90 && longitude >= -180 && longitude <= 180
    if (!coordinates && !hasManualCoordinates) { Alert.alert("Add a location", "Use GPS, or enter valid latitude and longitude coordinates. A landmark can provide context, but does not replace a location pin."); return }
    const affectedCount = people.trim() ? Number(people) : undefined
    const trappedCount = trapped.trim() ? Number(trapped) : undefined
    if ((affectedCount !== undefined && (!Number.isInteger(affectedCount) || affectedCount < 0)) || (trappedCount !== undefined && (!Number.isInteger(trappedCount) || trappedCount < 0))) { Alert.alert("Check the people counts", "Enter a whole number of zero or more, or leave the field blank."); return }
    setBusy(true)
    try {
      const reportLocation = coordinates ?? { latitude, longitude, source: "manual" as const }
      const created = await createReport({ category, description: description.trim(), address: address.trim() || locationText || "Manually entered coordinates", location: reportLocation, peopleAffected: affectedCount, peopleTrapped: trappedCount, personallyInDanger: inDanger })
      setReportId(created.id)
      setReportStatus(created.status || "Submitted")
      setSubmittedAt(created.submittedAt || new Date().toISOString())
      setBusy(false)
      if (attachments.length) {
        setMediaProgress(`Uploading 0 of ${attachments.length} attachments…`)
        void (async () => {
          for (const [index, file] of attachments.entries()) {
            try { await uploadReportMedia(created.id, file); setMediaProgress(`Uploading ${index + 1} of ${attachments.length} attachments…`) }
            catch { setMediaProgress("Report submitted. One or more attachments could not be uploaded; attach them again from report details when connected."); return }
          }
          setMediaProgress(`${attachments.length} attachment${attachments.length === 1 ? "" : "s"} uploaded.`)
        })()
      }
    } catch { Alert.alert("Could not submit", "Check your connection and try again. If urgent, use verified local emergency services.") }
    finally { setBusy(false) }
  }

  if (reportId) return (
    <SafeAreaView style={styles.safe}><View style={styles.confirmation}><Text style={styles.confirmIcon}>✓</Text><Text style={styles.eyebrow}>REPORT RECEIVED</Text><Text style={styles.title}>Your report is in the queue.</Text><Text style={styles.body}>The response status shown here comes from the backend. This prototype has not confirmed a dispatch.</Text><View style={styles.summary}><Text style={styles.label}>REPORT ID</Text><Text style={styles.value}>{reportId}</Text><Text style={[styles.label, { marginTop: 16 }]}>STATUS</Text><Text style={styles.value}>{reportStatus}</Text></View>{mediaProgress ? <Text accessibilityLiveRegion="polite" style={styles.hint}>{mediaProgress}</Text> : null}<Pressable style={styles.submit} onPress={() => router.replace("/")}><Text style={styles.submitText}>Back to home</Text></Pressable><Text style={styles.disclaimer}>Submission time: {submittedAt ? new Date(submittedAt).toLocaleString() : "Just now"}</Text></View></SafeAreaView>
  )

  return (
    <SafeAreaView style={styles.safe}><ScrollView contentContainerStyle={styles.form}>
      <View style={styles.demoTag}><Text style={styles.demoText}>GUEST REPORTING · NO ACCOUNT REQUIRED</Text></View>
      <Text style={styles.title}>What is happening?</Text><Text style={styles.body}>Share what you can. A category and location are enough to send an SOS.</Text>
      <Text style={styles.label}>EMERGENCY CATEGORY</Text><View style={styles.categoryList}>{EMERGENCY_CATEGORIES.map((item) => <Pressable key={item} onPress={() => setCategory(item)} style={[styles.chip, category === item && styles.chipActive]}><Text style={[styles.chipText, category === item && styles.chipTextActive]}>{item}</Text></Pressable>)}</View>
      <Text style={styles.label}>YOUR LOCATION</Text><View style={styles.locationBox}><TextInput style={styles.input} placeholder="GPS, coordinates or nearby landmark" value={locationText} onChangeText={(value) => { setLocationText(value); setCoordinates(null) }} accessibilityLabel="Location or landmark" /><Pressable onPress={locate} style={styles.inlineButton}><Text style={styles.link}>Use GPS</Text></Pressable></View><TextInput style={styles.input} placeholder="Address or landmark (optional)" value={address} onChangeText={setAddress} accessibilityLabel="Address or landmark" /><Text style={styles.hint}>{coordinates ? `GPS location · ±${Math.round(coordinates.accuracyMeters ?? 0)} m` : "Manual coordinates are clearly marked; enter a map pin below."}</Text>{!coordinates ? <View style={styles.numberRow}><TextInput style={styles.input} placeholder="Latitude" value={manualLatitude} onChangeText={setManualLatitude} keyboardType="decimal-pad" accessibilityLabel="Manual latitude" /><TextInput style={styles.input} placeholder="Longitude" value={manualLongitude} onChangeText={setManualLongitude} keyboardType="decimal-pad" accessibilityLabel="Manual longitude" /></View> : null}
      <Text style={styles.label}>SHORT DESCRIPTION · OPTIONAL</Text><TextInput style={[styles.input, styles.multiline]} placeholder="What can responders see or hear?" value={description} onChangeText={setDescription} multiline maxLength={500} textAlignVertical="top" accessibilityLabel="Short emergency description" />
      <Text style={styles.label}>PEOPLE AFFECTED · IF KNOWN</Text><View style={styles.numberRow}><TextInput style={styles.input} placeholder="Affected" value={people} onChangeText={setPeople} keyboardType="number-pad" accessibilityLabel="People affected" /><TextInput style={styles.input} placeholder="Trapped or injured" value={trapped} onChangeText={setTrapped} keyboardType="number-pad" accessibilityLabel="People trapped or injured" /></View>
      <Text style={styles.label}>ARE YOU PERSONALLY IN DANGER?</Text><View style={styles.numberRow}>{[{ label: "Yes", value: true }, { label: "No", value: false }, { label: "Unsure", value: undefined }].map(({ label, value }) => <Pressable key={label} onPress={() => setInDanger(value)} style={[styles.chip, inDanger === value && styles.chipActive]}><Text style={[styles.chipText, inDanger === value && styles.chipTextActive]}>{label}</Text></Pressable>)}</View>
      <Text style={styles.label}>ADD MEDIA · OPTIONAL</Text><View style={styles.numberRow}><Pressable onPress={() => selectImage(true)} style={styles.mediaButton}><Text style={styles.mediaText}>Take photo</Text></Pressable><Pressable onPress={() => selectImage(false)} style={styles.mediaButton}><Text style={styles.mediaText}>Image / video</Text></Pressable><Pressable onPress={toggleRecording} style={styles.mediaButton}><Text style={styles.mediaText}>{recordingState.isRecording ? "Stop audio" : "Record audio"}</Text></Pressable></View><Text style={styles.hint}>{attachments.length ? `${attachments.length} attachment${attachments.length === 1 ? "" : "s"} queued` : "Camera, gallery, video and voice note are optional."}</Text>
      <Pressable disabled={busy} onPress={submit} style={[styles.submit, busy && styles.disabled]}><Text style={styles.submitText}>{busy ? "Submitting…" : "Submit SOS report"}</Text></Pressable><Text style={styles.disclaimer}>For immediate danger, contact verified local emergency services. This app does not replace emergency services.</Text>
    </ScrollView></SafeAreaView>
  )
}

const styles = StyleSheet.create({ safe: { flex: 1, backgroundColor: "#f5f7f8" }, form: { padding: 18, paddingBottom: 42, gap: 10, maxWidth: 600, width: "100%", alignSelf: "center" }, demoTag: { alignSelf: "flex-start", backgroundColor: "#fff4dd", paddingHorizontal: 10, paddingVertical: 6, borderRadius: 7 }, demoText: { color: "#8f601f", fontSize: 9, fontWeight: "800", letterSpacing: 0.8 }, title: { color: BRAND.colors.ink, fontSize: 26, fontWeight: "800", marginTop: 4 }, body: { color: "#65737e", fontSize: 13, lineHeight: 19, marginBottom: 6 }, label: { color: "#64727d", fontWeight: "800", fontSize: 10, letterSpacing: 1, marginTop: 8 }, categoryList: { flexDirection: "row", flexWrap: "wrap", gap: 7 }, chip: { paddingHorizontal: 11, paddingVertical: 9, borderRadius: 9, backgroundColor: "#fff", borderWidth: 1, borderColor: "#dfe5e8" }, chipActive: { borderColor: BRAND.colors.red, backgroundColor: "#fff0ef" }, chipText: { color: "#475660", fontWeight: "600", fontSize: 11 }, chipTextActive: { color: "#a82d32" }, locationBox: { flexDirection: "row", alignItems: "center", gap: 8 }, input: { flex: 1, backgroundColor: "#fff", borderWidth: 1, borderColor: "#dfe5e8", borderRadius: 10, paddingHorizontal: 12, paddingVertical: 12, fontSize: 13, color: BRAND.colors.ink }, inlineButton: { backgroundColor: "#eaf4f7", paddingHorizontal: 11, paddingVertical: 12, borderRadius: 10 }, link: { color: "#167993", fontWeight: "800", fontSize: 11 }, hint: { color: "#78858f", fontSize: 10, marginTop: -4 }, multiline: { minHeight: 94 }, numberRow: { flexDirection: "row", gap: 8, flexWrap: "wrap" }, mediaButton: { flex: 1, minWidth: 88, backgroundColor: "#fff", borderWidth: 1, borderColor: "#dfe5e8", borderRadius: 10, padding: 12, alignItems: "center" }, mediaText: { color: "#32424d", fontSize: 11, fontWeight: "700" }, submit: { marginTop: 8, paddingVertical: 16, borderRadius: 12, backgroundColor: BRAND.colors.red, alignItems: "center" }, submitText: { color: "#fff", fontSize: 14, fontWeight: "800" }, disabled: { opacity: 0.55 }, disclaimer: { color: "#78858f", textAlign: "center", fontSize: 10, lineHeight: 15, marginTop: 2 }, confirmation: { flex: 1, padding: 28, justifyContent: "center", maxWidth: 500, width: "100%", alignSelf: "center" }, confirmIcon: { backgroundColor: "#e8f5ef", color: "#3c896c", width: 48, height: 48, textAlign: "center", textAlignVertical: "center", borderRadius: 24, overflow: "hidden", fontSize: 24, fontWeight: "800", marginBottom: 22 }, eyebrow: { color: "#3c896c", fontSize: 10, fontWeight: "800", letterSpacing: 1.5 }, summary: { marginTop: 20, padding: 18, backgroundColor: "#fff", borderWidth: 1, borderColor: "#e1e7ea", borderRadius: 12 }, value: { color: BRAND.colors.ink, fontSize: 14, fontWeight: "700", marginTop: 6 } })
