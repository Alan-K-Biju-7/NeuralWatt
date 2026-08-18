import { StyleSheet, Text, View } from "react-native";
import { colors } from "@/theme/colors";

export function Metric({ label, value, accent = false }: { label: string; value: string; accent?: boolean }) {
  return <View style={styles.wrap}><Text style={styles.label}>{label}</Text><Text style={[styles.value, accent && styles.accent]}>{value}</Text></View>;
}

const styles = StyleSheet.create({
  wrap: { flex: 1, minWidth: 120, gap: 4 },
  label: { color: colors.textMuted, fontSize: 12 },
  value: { color: colors.text, fontSize: 22, fontWeight: "800" },
  accent: { color: colors.primary },
});
