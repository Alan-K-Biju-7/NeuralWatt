import { StyleSheet, Text, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { colors } from "@/theme/colors";

export function EmptyState({ title, message }: { title: string; message: string }) {
  return <View style={styles.wrap}><Ionicons name="leaf-outline" size={34} color={colors.primary} /><Text style={styles.title}>{title}</Text><Text style={styles.message}>{message}</Text></View>;
}

const styles = StyleSheet.create({ wrap: { alignItems: "center", gap: 8, padding: 28 }, title: { color: colors.text, fontSize: 17, fontWeight: "700" }, message: { color: colors.textMuted, lineHeight: 20, textAlign: "center" } });
