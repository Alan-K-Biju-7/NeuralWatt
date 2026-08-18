import { StyleSheet, Text, View } from "react-native";
import { AppButton } from "@/components/AppButton";
import { colors } from "@/theme/colors";

export function ErrorState({ message, retry }: { message: string; retry?: () => void }) {
  return <View style={styles.wrap}><Text style={styles.title}>We couldn’t load this</Text><Text style={styles.message}>{message}</Text>{retry ? <AppButton label="Try again" onPress={retry} variant="secondary" /> : null}</View>;
}

const styles = StyleSheet.create({ wrap: { gap: 12, paddingVertical: 28 }, title: { color: colors.text, fontSize: 18, fontWeight: "700" }, message: { color: colors.textMuted, lineHeight: 20 } });
