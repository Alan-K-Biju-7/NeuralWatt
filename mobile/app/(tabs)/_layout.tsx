import { Ionicons } from "@expo/vector-icons";
import { Redirect, Tabs } from "expo-router";
import { useAuthStore } from "@/store/authStore";
import { colors } from "@/theme/colors";

const icons: Record<string, keyof typeof Ionicons.glyphMap> = { index: "flash", analytics: "bar-chart", insights: "bulb", alerts: "notifications", settings: "settings" };

export default function TabsLayout() {
  const { user, isRestoring } = useAuthStore();
  if (!isRestoring && !user) return <Redirect href="/(auth)/login" />;
  return <Tabs screenOptions={({ route }) => ({ headerShown: false, tabBarActiveTintColor: colors.primary, tabBarInactiveTintColor: colors.textMuted, tabBarStyle: { backgroundColor: colors.surface, borderTopColor: colors.border, height: 68, paddingBottom: 8 }, tabBarIcon: ({ color, size }) => <Ionicons name={icons[route.name] ?? "ellipse"} color={color} size={size} /> })}><Tabs.Screen name="index" options={{ title: "Home" }} /><Tabs.Screen name="analytics" options={{ title: "Usage" }} /><Tabs.Screen name="insights" options={{ title: "Insights" }} /><Tabs.Screen name="alerts" options={{ title: "Alerts" }} /><Tabs.Screen name="settings" options={{ title: "Settings" }} /></Tabs>;
}
