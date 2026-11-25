import { ScrollView, StyleSheet, Text, View } from "react-native"
import { SafeAreaView } from "react-native-safe-area-context"
import { BRAND } from "../../shared/design-system"

const guidance = [
  ["Move away from immediate danger", "If it is safe to do so, move to a clear area and follow instructions from qualified responders."],
  ["Share your location", "Use GPS or enter a nearby landmark. You can submit a report without an account."],
  ["Keep yourself safe", "Do not enter damaged buildings, floodwater, fire areas, or other restricted zones to gather information."],
  ["Emergency contacts", "No local emergency number is configured for this prototype. Use verified local emergency services for immediate danger."],
]

export default function SafetyScreen() {
  return <SafeAreaView style={styles.safe}><ScrollView contentContainerStyle={styles.wrap}><View style={styles.notice}><Text style={styles.noticeTitle}>This app does not replace emergency services.</Text><Text style={styles.body}>For immediate danger, contact verified local emergency services. CIRRUS is a reporting prototype and does not dispatch responders.</Text></View>{guidance.map(([title, body], index) => <View key={title} style={styles.card}><Text style={styles.number}>{String(index + 1).padStart(2, "0")}</Text><View style={{ flex: 1 }}><Text style={styles.title}>{title}</Text><Text style={styles.body}>{body}</Text></View></View>)}</ScrollView></SafeAreaView>
}
const styles = StyleSheet.create({ safe: { flex: 1, backgroundColor: "#f5f7f8" }, wrap: { padding: 20, gap: 12, maxWidth: 560, width: "100%", alignSelf: "center" }, notice: { padding: 16, backgroundColor: "#fff2f1", borderWidth: 1, borderColor: "#f1cecc", borderRadius: 12 }, noticeTitle: { color: "#9e3033", fontWeight: "800", fontSize: 14, marginBottom: 6 }, body: { color: "#65737e", fontSize: 12, lineHeight: 18, marginTop: 5 }, card: { backgroundColor: "#fff", borderWidth: 1, borderColor: "#e4e9ec", borderRadius: 12, padding: 15, flexDirection: "row", gap: 13 }, number: { color: BRAND.colors.red, fontWeight: "800", fontSize: 11 }, title: { color: BRAND.colors.ink, fontWeight: "800", fontSize: 13 } })
