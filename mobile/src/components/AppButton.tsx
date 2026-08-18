import { ActivityIndicator, Pressable, StyleSheet, Text } from "react-native";
import { colors } from "@/theme/colors";

type Props = { label: string; onPress: () => void; loading?: boolean; disabled?: boolean; variant?: "primary" | "secondary" };

export function AppButton({ label, onPress, loading, disabled, variant = "primary" }: Props) {
  const secondary = variant === "secondary";
  return (
    <Pressable accessibilityRole="button" disabled={disabled || loading} onPress={onPress} style={({ pressed }) => [styles.button, secondary && styles.secondary, pressed && styles.pressed, (disabled || loading) && styles.disabled]}>
      {loading ? <ActivityIndicator color={secondary ? colors.primary : colors.background} /> : <Text style={[styles.label, secondary && styles.secondaryLabel]}>{label}</Text>}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: { minHeight: 52, borderRadius: 16, backgroundColor: colors.primary, alignItems: "center", justifyContent: "center", paddingHorizontal: 20 },
  secondary: { backgroundColor: colors.surfaceRaised, borderWidth: 1, borderColor: colors.border },
  label: { color: colors.background, fontSize: 16, fontWeight: "700" },
  secondaryLabel: { color: colors.primary },
  pressed: { opacity: 0.82 },
  disabled: { opacity: 0.5 },
});
