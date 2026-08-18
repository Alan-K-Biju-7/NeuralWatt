import { router } from "expo-router";
import { StyleSheet, Text, View } from "react-native";
import { AppButton } from "@/components/AppButton";
import { EnergyCard } from "@/components/EnergyCard";
import { Screen } from "@/components/Screen";
import { useHousehold } from "@/hooks/useHousehold";
import { queryClient } from "@/lib/queryClient";
import { useAuthStore } from "@/store/authStore";
import { colors } from "@/theme/colors";

export default function SettingsScreen() {
  const { user, signOut } = useAuthStore(); const { household, device } = useHousehold();
  const logout = async () => { await signOut(); queryClient.clear(); router.replace("/(auth)/login"); };
  return <Screen><Text style={styles.title}>Settings</Text><EnergyCard title="Account"><Text style={styles.name}>{user?.full_name}</Text><Text style={styles.muted}>{user?.email}</Text></EnergyCard><EnergyCard title="Energy connection"><View style={styles.line}><Text style={styles.label}>Household</Text><Text style={styles.value}>{household?.name ?? "Not connected"}</Text></View><View style={styles.line}><Text style={styles.label}>Active device</Text><Text style={styles.value}>{device?.name ?? "None"}</Text></View><View style={styles.line}><Text style={styles.label}>Rated power</Text><Text style={styles.value}>{device ? `${device.rated_power_watts} W` : "—"}</Text></View></EnergyCard><Text style={styles.note}>Household and device provisioning remains available in the full React dashboard.</Text><AppButton label="Sign out" onPress={logout} variant="secondary" /></Screen>;
}

const styles = StyleSheet.create({ title: { color: colors.text, fontSize: 31, fontWeight: "800" }, name: { color: colors.text, fontSize: 19, fontWeight: "700" }, muted: { color: colors.textMuted }, line: { flexDirection: "row", justifyContent: "space-between", gap: 18 }, label: { color: colors.textMuted }, value: { color: colors.text, fontWeight: "600", flexShrink: 1, textAlign: "right" }, note: { color: colors.textMuted, lineHeight: 20 } });
