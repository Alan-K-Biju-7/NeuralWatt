import { StyleSheet, Text, TextInput, type TextInputProps, View } from "react-native";
import { colors } from "@/theme/colors";

type Props = TextInputProps & { label: string; error?: string };

export function AppInput({ label, error, ...props }: Props) {
  return <View style={styles.wrap}><Text style={styles.label}>{label}</Text><TextInput placeholderTextColor={colors.textMuted} style={[styles.input, error && styles.invalid]} {...props} />{error ? <Text style={styles.error}>{error}</Text> : null}</View>;
}

const styles = StyleSheet.create({
  wrap: { gap: 7 },
  label: { color: colors.textMuted, fontSize: 13, fontWeight: "600" },
  input: { minHeight: 52, borderRadius: 14, borderWidth: 1, borderColor: colors.border, backgroundColor: colors.surface, color: colors.text, paddingHorizontal: 16, fontSize: 16 },
  invalid: { borderColor: colors.danger },
  error: { color: colors.danger, fontSize: 12 },
});
