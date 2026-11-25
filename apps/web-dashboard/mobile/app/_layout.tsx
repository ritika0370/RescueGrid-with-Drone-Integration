import { Stack } from "expo-router"
import { StatusBar } from "expo-status-bar"
import { BRAND } from "../../shared/design-system"

export default function RootLayout() {
  return (
    <>
      <StatusBar style="dark" />
      <Stack screenOptions={{ headerTintColor: BRAND.colors.ink, headerTitleStyle: { fontWeight: "700" }, contentStyle: { backgroundColor: "#f5f7f8" } }}>
        <Stack.Screen name="index" options={{ title: "CIRRUS · Citizen", headerShown: false }} />
        <Stack.Screen name="report" options={{ title: "Report an emergency", presentation: "modal" }} />
        <Stack.Screen name="my-reports" options={{ title: "My reports" }} />
        <Stack.Screen name="safety" options={{ title: "Safety information" }} />
        <Stack.Screen name="account" options={{ title: "Account" }} />
      </Stack>
    </>
  )
}
