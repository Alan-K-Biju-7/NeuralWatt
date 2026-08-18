import { ActivityIndicator, StyleSheet, Text, View } from "react-native";
import { colors } from "@/theme/colors";

export function LoadingState({ label = "Loading your energy data…" }: { label?: string }) {
  return <View style={styles.wrap}><ActivityIndicator size="large" color={colors.primary} /><Text style={styles.label}>{label}</Text></View>;
}

const styles = StyleSheet.create({ wrap: { flex: 1, alignItems: "center", justifyContent: "center", gap: 14, padding: 32 }, label: { color: colors.textMuted } });
