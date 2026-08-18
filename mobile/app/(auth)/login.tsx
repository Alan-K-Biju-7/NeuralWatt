import { useState } from "react";
import { Link, router } from "expo-router";
import { StyleSheet, Text, View } from "react-native";
import { AppButton } from "@/components/AppButton";
import { AppInput } from "@/components/AppInput";
import { Screen } from "@/components/Screen";
import { getApiErrorMessage } from "@/lib/apiClient";
import { authService } from "@/services/auth";
import { useAuthStore } from "@/store/authStore";
import { colors } from "@/theme/colors";

export default function LoginScreen() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const setSession = useAuthStore((state) => state.setSession);

  const submit = async () => {
    if (!email.trim() || !password) return setError("Enter your email and password.");
    setLoading(true); setError("");
    try {
      const session = await authService.login({ email: email.trim().toLowerCase(), password });
      await setSession(session.access_token, session.user);
      router.replace("/(tabs)");
    } catch (reason) { setError(getApiErrorMessage(reason)); }
    finally { setLoading(false); }
  };

  return <Screen><View style={styles.hero}><Text style={styles.eyebrow}>NEURALWATT</Text><Text style={styles.title}>Your home energy, in your pocket.</Text><Text style={styles.copy}>Watch live demand, understand costs, and catch unusual usage early.</Text></View><View style={styles.form}><AppInput label="Email" value={email} onChangeText={setEmail} keyboardType="email-address" autoCapitalize="none" autoComplete="email" /><AppInput label="Password" value={password} onChangeText={setPassword} secureTextEntry autoComplete="current-password" />{error ? <Text style={styles.error}>{error}</Text> : null}<AppButton label="Sign in" onPress={submit} loading={loading} /><Text style={styles.linkCopy}>New to NeuralWatt? <Link href="/(auth)/register" style={styles.link}>Create an account</Link></Text></View></Screen>;
}

const styles = StyleSheet.create({ hero: { marginTop: 42, gap: 12 }, eyebrow: { color: colors.primary, fontSize: 13, fontWeight: "800", letterSpacing: 2 }, title: { color: colors.text, fontSize: 38, lineHeight: 44, fontWeight: "800" }, copy: { color: colors.textMuted, fontSize: 16, lineHeight: 24 }, form: { marginTop: 22, gap: 16 }, error: { color: colors.danger }, linkCopy: { color: colors.textMuted, textAlign: "center" }, link: { color: colors.primary, fontWeight: "700" } });
