import { router } from "expo-router"
import * as Location from "expo-location"
import { useState } from "react"
import { Alert, Pressable, ScrollView, StyleSheet, Text, View } from "react-native"
import { SafeAreaView } from "react-native-safe-area-context"
import { EMERGENCY_CATEGORIES } from "../../shared/types"
import { BRAND } from "../../shared/design-system"

const categoryMarks = ["F", "W", "E", "B", "R", "M", "P", "+"]

export default function HomeScreen() {
  const [position, setPosition] = useState<string | null>(null)
  const [gpsCoordinates, setGpsCoordinates] = useState<{ latitude: number; longitude: number; accuracyMeters: number } | null>(null)
  const [category, setCategory] = useState<string>("Other emergency")

  async function requestLocation() {
    try {
      const permission = await Location.requestForegroundPermissionsAsync()
      if (permission.status !== "granted") {
        setPosition("Location unavailable · choose manually in your report")
        return
      }
      const result = await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.Balanced })
      const accuracyMeters = result.coords.accuracy ?? 0
      setGpsCoordinates({ latitude: result.coords.latitude, longitude: result.coords.longitude, accuracyMeters })
      setPosition(`${result.coords.latitude.toFixed(5)}, ${result.coords.longitude.toFixed(5)} · ±${Math.round(accuracyMeters)} m`)
    } catch {
      setPosition("Location unavailable · choose manually in your report")
    }
  }

  function openReport(selectedCategory = category) {
    router.push({ pathname: "/report", params: { category: selectedCategory, location: position ?? "", latitude: gpsCoordinates?.latitude.toString() ?? "", longitude: gpsCoordinates?.longitude.toString() ?? "", accuracyMeters: gpsCoordinates?.accuracyMeters.toString() ?? "" } })
  }

  return (
    <SafeAreaView style={styles.safe}>
      <ScrollView contentContainerStyle={styles.container}>
        <View style={styles.topRow}>
          <View><Text style={styles.wordmark}>CIRRUS</Text><Text style={styles.kicker}>RESPONSE COORDINATION</Text></View>
          <View style={styles.prototype}><Text style={styles.protoText}>PROTOTYPE</Text></View>
        </View>
        <View style={styles.welcome}><Text style={styles.eyebrow}>CITIZEN REPORTING</Text><Text style={styles.title}>Help starts{`\n`}with a report.</Text><Text style={styles.copy}>A simple way to share what is happening and where you need help.</Text></View>
        <Pressable accessibilityRole="button" accessibilityLabel="Start an emergency SOS report" onPress={() => openReport()} style={styles.sos}>
          <Text style={styles.sosLabel}>SOS</Text><Text style={styles.sosText}>Tap to report an emergency</Text>
        </Pressable>
        <View style={styles.locationCard}>
          <View style={styles.pin}><Text style={{ color: BRAND.colors.blue }}>⌖</Text></View>
          <View style={{ flex: 1 }}><Text style={styles.cardTitle}>Your location</Text><Text style={styles.muted}>{position ?? "Not shared yet · optional"}</Text></View>
          <Pressable onPress={requestLocation} accessibilityRole="button"><Text style={styles.link}>Use GPS</Text></Pressable>
        </View>
        <View style={styles.sectionHeading}><Text style={styles.sectionTitle}>Choose a category</Text><Text style={styles.muted}>You can change this later</Text></View>
        <View style={styles.categories}>{EMERGENCY_CATEGORIES.map((item, index) => (
          <Pressable key={item} onPress={() => { setCategory(item); openReport(item) }} style={styles.category} accessibilityRole="button" accessibilityLabel={`Report ${item}`}>
            <View style={styles.categoryMark}><Text style={styles.categoryMarkText}>{categoryMarks[index]}</Text></View><Text style={styles.categoryText}>{item}</Text>
          </Pressable>
        ))}</View>
        <View style={styles.reportsHeader}><Text style={styles.sectionTitle}>Recent reports</Text><Pressable onPress={() => router.push("/my-reports")}><Text style={styles.link}>View all</Text></Pressable></View>
        <View style={styles.empty}><Text style={styles.emptyTitle}>No reports yet</Text><Text style={styles.muted}>Your submitted reports will appear here.</Text></View>
        <View style={styles.footerLinks}><Pressable onPress={() => router.push("/safety")}><Text style={styles.link}>Safety information</Text></Pressable><Text style={styles.muted}> · </Text><Pressable onPress={() => router.push("/account")}><Text style={styles.link}>Sign in / register</Text></Pressable></View>
        <Text style={styles.disclaimer}>CIRRUS does not replace verified local emergency services.</Text>
      </ScrollView>
    </SafeAreaView>
  )
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: "#f5f7f8" }, container: { padding: 20, paddingBottom: 40, maxWidth: 560, width: "100%", alignSelf: "center" },
  topRow: { flexDirection: "row", justifyContent: "space-between", alignItems: "center" }, wordmark: { fontSize: 20, fontWeight: "900", letterSpacing: 2.2, color: BRAND.colors.ink }, kicker: { color: "#6d7b87", fontSize: 9, fontWeight: "700", letterSpacing: 1.4, marginTop: 3 }, prototype: { borderWidth: 1, borderColor: "#e9c37e", backgroundColor: "#fff8e9", paddingHorizontal: 9, paddingVertical: 6, borderRadius: 7 }, protoText: { color: "#885a19", fontWeight: "800", fontSize: 9, letterSpacing: 0.7 },
  welcome: { paddingTop: 28, paddingBottom: 20 }, eyebrow: { fontSize: 10, fontWeight: "800", color: BRAND.colors.red, letterSpacing: 1.6 }, title: { color: BRAND.colors.ink, fontSize: 34, lineHeight: 38, fontWeight: "800", marginTop: 7 }, copy: { fontSize: 14, color: "#667581", lineHeight: 20, marginTop: 9, maxWidth: 320 },
  sos: { minHeight: 144, backgroundColor: BRAND.colors.red, borderRadius: 18, alignItems: "center", justifyContent: "center", shadowColor: "#9b2830", shadowOpacity: 0.18, shadowRadius: 16, elevation: 3 }, sosLabel: { color: "#fff", fontSize: 40, fontWeight: "900", letterSpacing: 2 }, sosText: { color: "#fff", opacity: 0.94, marginTop: 4, fontSize: 14, fontWeight: "600" },
  locationCard: { marginTop: 14, padding: 13, backgroundColor: "#fff", borderRadius: 13, flexDirection: "row", alignItems: "center", gap: 10, borderWidth: 1, borderColor: "#e6eaed" }, pin: { width: 34, height: 34, borderRadius: 10, backgroundColor: "#eaf4f7", alignItems: "center", justifyContent: "center" }, cardTitle: { color: BRAND.colors.ink, fontWeight: "700", fontSize: 12 }, muted: { color: "#77848e", fontSize: 11, lineHeight: 16, marginTop: 3 }, link: { color: "#167993", fontWeight: "700", fontSize: 12 },
  sectionHeading: { marginTop: 23, marginBottom: 11 }, sectionTitle: { color: BRAND.colors.ink, fontSize: 15, fontWeight: "800" }, categories: { flexDirection: "row", flexWrap: "wrap", gap: 8 }, category: { width: "48%", minHeight: 68, flexGrow: 1, flexDirection: "row", alignItems: "center", gap: 10, paddingHorizontal: 10, backgroundColor: "#fff", borderRadius: 12, borderWidth: 1, borderColor: "#e6eaed" }, categoryMark: { width: 28, height: 28, borderRadius: 9, backgroundColor: "#eef1f4", alignItems: "center", justifyContent: "center" }, categoryMarkText: { color: "#60717c", fontSize: 11, fontWeight: "900" }, categoryText: { color: BRAND.colors.ink, fontSize: 12, fontWeight: "700", flexShrink: 1 }, reportsHeader: { marginTop: 23, marginBottom: 10, flexDirection: "row", alignItems: "center", justifyContent: "space-between" }, empty: { backgroundColor: "#fff", borderRadius: 12, padding: 17, borderWidth: 1, borderColor: "#e6eaed" }, emptyTitle: { color: BRAND.colors.ink, fontSize: 12, fontWeight: "700" }, footerLinks: { flexDirection: "row", alignItems: "center", justifyContent: "center", marginTop: 20 }, disclaimer: { textAlign: "center", fontSize: 10, color: "#7d8991", marginTop: 10, lineHeight: 15 },
})
