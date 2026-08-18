import type { PropsWithChildren } from "react";
import { StyleSheet, Text, View } from "react-native";
import { colors } from "@/theme/colors";

export function EnergyCard({ title, children }: PropsWithChildren<{ title?: string }>) {
  return <View style={styles.card}>{title ? <Text style={styles.title}>{title}</Text> : null}{children}</View>;
}

const styles = StyleSheet.create({
  card: { borderRadius: 20, borderWidth: 1, borderColor: colors.border, backgroundColor: colors.surface, padding: 18, gap: 12 },
  title: { color: colors.text, fontSize: 16, fontWeight: "700" },
});
