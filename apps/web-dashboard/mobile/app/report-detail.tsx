import { router, useLocalSearchParams } from "expo-router"
import * as ImagePicker from "expo-image-picker"
import { AudioModule, RecordingPresets, useAudioRecorder, useAudioRecorderState } from "expo-audio"
import { useEffect, useState } from "react"
import { ActivityIndicator, Alert, Image, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from "react-native"
import { SafeAreaView } from "react-native-safe-area-context"
import { BRAND } from "../../shared/design-system"
import { addReportUpdate, CitizenReportDetail, getReportDetails, getReportStatus, uploadReportMedia } from "../src/api"

export default function ReportDetailScreen() {
  const { id } = useLocalSearchParams<{ id?: string }>()
  const [report, setReport] = useState<CitizenReportDetail | null>(null)
  const [updates, setUpdates] = useState<Array<{ at: string; text: string }>>([])
  const [note, setNote] = useState("")
  const [attachments, setAttachments] = useState<Array<{ uri: string; name: string; type: string }>>([])
  const [busy, setBusy] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)
  const recorder = useAudioRecorder(RecordingPresets.HIGH_QUALITY)
  const recordingState = useAudioRecorderState(recorder)

  async function load() {
    if (!id) { setError(true); setLoading(false); return }
    try {
      const [details, status] = await Promise.all([getReportDetails(id), getReportStatus(id)])
      setReport({ ...details, status: status.status || details.status })
      setUpdates(status.updates ?? [])
      setError(false)
    } catch { setError(true) } finally { setLoading(false) }
  }

  useEffect(() => { void load() }, [id])

  async function chooseMedia(fromCamera: boolean) {
    try {
      const permission = fromCamera ? await ImagePicker.requestCameraPermissionsAsync() : await ImagePicker.requestMediaLibraryPermissionsAsync()
      if (!permission.granted) { Alert.alert("Permission needed", "You can still submit a text update without media."); return }
      const result = fromCamera
        ? await ImagePicker.launchCameraAsync({ mediaTypes: ["images"], quality: 0.7 })
        : await ImagePicker.launchImageLibraryAsync({ mediaTypes: ["images", "videos"], quality: 0.7 })
      if (!result.canceled) setAttachments((items) => [...items, ...result.assets.map((asset) => ({ uri: asset.uri, name: asset.fileName || `update-${items.length + 1}`, type: asset.mimeType || "image/jpeg" }))])
    } catch { Alert.alert("Media unavailable", "You can still submit a text update.") }
  }

  async function toggleAudio() {
    try {
      if (recordingState.isRecording) {
        await recorder.stop()
        if (recorder.uri) setAttachments((items) => [...items, { uri: recorder.uri!, name: "follow-up-audio.m4a", type: "audio/m4a" }])
      } else {
        const permission = await AudioModule.requestRecordingPermissionsAsync()
        if (!permission.granted) { Alert.alert("Microphone permission not granted", "You can still submit a text update."); return }
        await recorder.prepareToRecordAsync()
        recorder.record()
      }
    } catch { Alert.alert("Audio unavailable", "You can still submit a text update.") }
  }

  async function submitUpdate() {
    if (!id || (!note.trim() && attachments.length === 0)) return
    setBusy(true)
    try {
      if (note.trim()) {
        await addReportUpdate(id, note.trim())
        setNote("")
      }
      for (const file of attachments) await uploadReportMedia(id, file)
      setNote("")
      setAttachments([])
      await load()
    } catch { Alert.alert("Update not sent", "Check your connection. Your original report remains unchanged.") }
    finally { setBusy(false) }
  }

  if (loading) return <SafeAreaView style={styles.safe}><ActivityIndicator style={{ marginTop: 48 }} color={BRAND.colors.red} /></SafeAreaView>
  if (error || !report) return <SafeAreaView style={styles.safe}><View style={styles.content}><Text style={styles.title}>Report unavailable</Text><Text style={styles.copy}>The report could not be loaded. Check your connection and try again.</Text><Pressable accessibilityRole="button" onPress={() => { setLoading(true); void load() }} style={styles.secondary}><Text style={styles.secondaryText}>Try again</Text></Pressable><Pressable onPress={() => router.back()} style={styles.back}><Text style={styles.link}>Back to reports</Text></Pressable></View></SafeAreaView>

  return <SafeAreaView style={styles.safe}><ScrollView contentContainerStyle={styles.content}>
    <Pressable onPress={() => router.back()} style={styles.back}><Text style={styles.link}>‹  My reports</Text></Pressable>
    <Text style={styles.kicker}>EMERGENCY REPORT</Text><Text style={styles.title}>{report.category}</Text>
    <View style={styles.card}><Text style={styles.label}>REPORT ID</Text><Text style={styles.value}>{report.id}</Text><Text style={styles.label}>CURRENT STATUS</Text><Text style={styles.status}>{report.status}</Text><Text style={styles.label}>SUBMITTED</Text><Text style={styles.copy}>{new Date(report.submittedAt).toLocaleString()}</Text><Text style={styles.label}>LOCATION</Text><Text style={styles.copy}>{report.address || "Location details were not provided."}</Text>{report.location ? <Text style={styles.copy}>{report.location.latitude.toFixed(5)}, {report.location.longitude.toFixed(5)} · {report.location.source === "manual" ? "manually entered" : `GPS${report.location.accuracyMeters ? ` · ±${Math.round(report.location.accuracyMeters)} m` : ""}`}</Text> : null}<Text style={styles.label}>ORIGINAL DESCRIPTION</Text><Text style={styles.copy}>{report.description || "No description provided."}</Text></View>
    <Text style={styles.section}>Submitted media</Text>{report.media.length === 0 ? <Text style={styles.copy}>No media attached.</Text> : report.media.map((item, index) => <View key={`${item.name}-${index}`} style={styles.mediaCard}>{item.uri && item.type.startsWith("image/") ? <Image source={{ uri: item.uri }} style={styles.image} accessibilityLabel={`Uploaded evidence ${index + 1}`} /> : null}<Text style={styles.copy}>{item.name} · {item.type}</Text></View>)}
    <Text style={styles.section}>Status updates</Text>{updates.length === 0 ? <Text style={styles.copy}>No additional updates have been shared.</Text> : updates.map((item, index) => <View key={`${item.at}-${index}`} style={styles.updateCard}><Text style={styles.label}>{new Date(item.at).toLocaleString()}</Text><Text style={styles.copy}>{item.text}</Text></View>)}
    <Text style={styles.section}>Add information</Text><Text style={styles.copy}>New notes and media are appended. The original report is preserved.</Text><TextInput accessibilityLabel="Additional report information" value={note} onChangeText={setNote} placeholder="Add a new detail for responders…" maxLength={1000} multiline textAlignVertical="top" style={styles.input} /><View style={styles.mediaRow}><Pressable accessibilityRole="button" onPress={() => chooseMedia(true)} style={styles.secondary}><Text style={styles.secondaryText}>Take photo</Text></Pressable><Pressable accessibilityRole="button" onPress={() => chooseMedia(false)} style={styles.secondary}><Text style={styles.secondaryText}>Choose media</Text></Pressable><Pressable accessibilityRole="button" onPress={toggleAudio} style={styles.secondary}><Text style={styles.secondaryText}>{recordingState.isRecording ? "Stop recording" : "Record audio"}</Text></Pressable></View>{attachments.length > 0 ? <Text style={styles.copy}>{attachments.length} attachment{attachments.length === 1 ? "" : "s"} ready to upload.</Text> : null}<Pressable accessibilityRole="button" disabled={busy || (!note.trim() && attachments.length === 0)} onPress={submitUpdate} style={[styles.submit, (busy || (!note.trim() && attachments.length === 0)) && styles.disabled]}><Text style={styles.submitText}>{busy ? "Sending…" : "Add to report"}</Text></Pressable>
  </ScrollView></SafeAreaView>
}

const styles = StyleSheet.create({ safe: { flex: 1, backgroundColor: "#f5f7f8" }, content: { padding: 18, paddingBottom: 40, gap: 10, maxWidth: 600, width: "100%", alignSelf: "center" }, back: { alignSelf: "flex-start", paddingVertical: 8 }, link: { color: "#167993", fontWeight: "800", fontSize: 12 }, kicker: { color: "#8b2e31", fontSize: 10, fontWeight: "900", letterSpacing: 1.2, marginTop: 8 }, title: { color: BRAND.colors.ink, fontWeight: "800", fontSize: 26 }, section: { color: BRAND.colors.ink, fontWeight: "800", fontSize: 16, marginTop: 14 }, card: { backgroundColor: "#fff", borderWidth: 1, borderColor: "#e1e7ea", borderRadius: 13, padding: 16, gap: 7 }, label: { color: "#6e7a84", fontSize: 9, fontWeight: "900", letterSpacing: 1, marginTop: 8 }, value: { color: BRAND.colors.ink, fontSize: 13, fontWeight: "800" }, status: { color: "#356c5a", fontWeight: "800", fontSize: 13 }, copy: { color: "#697781", fontSize: 12, lineHeight: 18 }, mediaCard: { backgroundColor: "#fff", borderWidth: 1, borderColor: "#e1e7ea", borderRadius: 11, padding: 12, gap: 7 }, image: { width: "100%", height: 180, borderRadius: 8 }, updateCard: { borderLeftWidth: 3, borderLeftColor: BRAND.colors.red, paddingLeft: 12, paddingVertical: 8, gap: 5 }, input: { minHeight: 92, backgroundColor: "#fff", borderColor: "#dfe5e8", borderWidth: 1, borderRadius: 10, padding: 12, color: BRAND.colors.ink }, mediaRow: { flexDirection: "row", flexWrap: "wrap", gap: 7 }, secondary: { backgroundColor: "#fff", borderColor: "#dfe5e8", borderWidth: 1, paddingHorizontal: 12, paddingVertical: 11, borderRadius: 9 }, secondaryText: { color: BRAND.colors.ink, fontSize: 11, fontWeight: "700" }, submit: { backgroundColor: BRAND.colors.red, borderRadius: 11, alignItems: "center", paddingVertical: 15, marginTop: 5 }, submitText: { color: "#fff", fontWeight: "800", fontSize: 13 }, disabled: { opacity: 0.45 } })
