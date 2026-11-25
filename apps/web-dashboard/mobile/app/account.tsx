import { router } from "expo-router"
import { useState } from "react"
import { Alert, Pressable, StyleSheet, Text, TextInput, View } from "react-native"
import { SafeAreaView } from "react-native-safe-area-context"
import { BRAND } from "../../shared/design-system"
import { authenticate } from "../src/api"

export default function AccountScreen() {
  const [register, setRegister] = useState(false)
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [busy, setBusy] = useState(false)
  async function submit() {
    setBusy(true)
    try {
      await authenticate(register ? "register" : "login", { email: email.trim(), password })
      Alert.alert(register ? "Account created" : "Signed in", "Account access is provided by the connected backend.")
      router.replace("/")
    } catch {
      Alert.alert("Account service unavailable", "You can still submit an emergency report as a guest.")
    } finally { setBusy(false) }
  }
  return <SafeAreaView style={styles.safe}><View style={styles.wrap}><Text style={styles.brand}>CIRRUS</Text><Text style={styles.title}>{register ? "Create an account" : "Sign in"}</Text><Text style={styles.copy}>Account access is optional. Emergency reporting is always available to guests.</Text><Text style={styles.label}>EMAIL</Text><TextInput style={styles.input} autoCapitalize="none" keyboardType="email-address" value={email} onChangeText={setEmail} accessibilityLabel="Email" /><Text style={styles.label}>PASSWORD</Text><TextInput style={styles.input} secureTextEntry value={password} onChangeText={setPassword} accessibilityLabel="Password" /><Pressable style={styles.button} onPress={submit} disabled={busy}><Text style={styles.buttonText}>{busy ? "Please wait…" : register ? "Create account" : "Sign in"}</Text></Pressable><Pressable onPress={() => setRegister(!register)} style={{ padding: 12 }}><Text style={styles.link}>{register ? "Already have an account? Sign in" : "New here? Create an account"}</Text></Pressable><Pressable onPress={() => router.replace("/")} style={{ padding: 12 }}><Text style={styles.link}>Continue as guest</Text></Pressable></View></SafeAreaView>
}
const styles = StyleSheet.create({ safe: { flex: 1, backgroundColor: "#f5f7f8" }, wrap: { flex: 1, justifyContent: "center", padding: 24, maxWidth: 500, width: "100%", alignSelf: "center" }, brand: { color: BRAND.colors.ink, fontWeight: "900", letterSpacing: 2, fontSize: 20 }, title: { color: BRAND.colors.ink, fontWeight: "800", fontSize: 27, marginTop: 26 }, copy: { color: "#697781", fontSize: 13, lineHeight: 19, marginTop: 8, marginBottom: 25 }, label: { color: "#64727d", fontWeight: "800", fontSize: 10, letterSpacing: 1, marginBottom: 7, marginTop: 9 }, input: { backgroundColor: "#fff", borderWidth: 1, borderColor: "#dfe5e8", borderRadius: 10, padding: 13, color: BRAND.colors.ink }, button: { backgroundColor: BRAND.colors.ink, padding: 15, borderRadius: 11, alignItems: "center", marginTop: 20 }, buttonText: { color: "#fff", fontWeight: "800", fontSize: 13 }, link: { textAlign: "center", color: "#167993", fontWeight: "700", fontSize: 12 } })
