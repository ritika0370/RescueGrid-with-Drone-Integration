import { useEffect, useState } from "react"
import { router } from "expo-router"
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from "react-native"
import { SafeAreaView } from "react-native-safe-area-context"
import { BRAND } from "../../shared/design-system"
import { getMyReports } from "../src/api"

export default function MyReportsScreen() {
  const [reports, setReports] = useState<Array<{ id: string; category: string; status: string; submittedAt: string; address?: string }> | null>(null)
  const [error, setError] = useState(false)
  useEffect(() => { getMyReports().then(setReports).catch(() => { setError(true); setReports([]) }) }, [])
  return <SafeAreaView style={styles.safe}><ScrollView contentContainerStyle={styles.wrap}><Text style={styles.title}>My reports</Text><Text style={styles.copy}>Status updates are provided by the connected response backend.</Text>{reports === null ? <ActivityIndicator color={BRAND.colors.red} /> : error ? <View style={styles.card}><Text style={styles.head}>Reports unavailable</Text><Text style={styles.copy}>Check your connection and try again.</Text></View> : reports.length === 0 ? <View style={styles.card}><Text style={styles.head}>No reports to show</Text><Text style={styles.copy}>Your reports appear here after submission. Demo entries and new reports last for this app session only.</Text></View> : reports.map((report) => <Pressable key={report.id} accessibilityRole="button" accessibilityLabel={`Open ${report.category} report ${report.id}`} onPress={() => router.push({ pathname: "/report-detail", params: { id: report.id } })} style={styles.card}><Text style={styles.id}>{report.id}</Text><Text style={styles.head}>{report.category}</Text><Text style={styles.copy}>{report.address || "Location not provided"} · {new Date(report.submittedAt).toLocaleString()}</Text><Text style={styles.status}>{report.status}</Text></Pressable>)}</ScrollView></SafeAreaView>
}
const styles = StyleSheet.create({ safe: { flex: 1, backgroundColor: "#f5f7f8" }, wrap: { padding: 20, gap: 13, maxWidth: 560, width: "100%", alignSelf: "center" }, title: { color: BRAND.colors.ink, fontWeight: "800", fontSize: 26 }, copy: { color: "#697781", fontSize: 12, lineHeight: 18 }, card: { backgroundColor: "#fff", borderWidth: 1, borderColor: "#e4e9ec", borderRadius: 12, padding: 16 }, id: { fontSize: 10, color: "#73808a", fontWeight: "700" }, head: { fontSize: 15, fontWeight: "800", color: BRAND.colors.ink, marginTop: 5 }, status: { alignSelf: "flex-start", color: "#356c5a", backgroundColor: "#e8f5ef", borderRadius: 8, paddingHorizontal: 9, paddingVertical: 6, fontWeight: "700", fontSize: 11, marginTop: 12 } })
