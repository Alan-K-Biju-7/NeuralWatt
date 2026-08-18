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

export default function RegisterScreen() {
  const [name, setName] = useState(""); const [email, setEmail] = useState(""); const [password, setPassword] = useState("");
  const [error, setError] = useState(""); const [loading, setLoading] = useState(false);
  const setSession = useAuthStore((state) => state.setSession);
  const submit = async () => {
    if (!name.trim() || !email.trim() || password.length < 8) return setError("Add your name, email, and a password of at least 8 characters.");
    setLoading(true); setError("");
    try { const session = await authService.register({ full_name: name.trim(), email: email.trim().toLowerCase(), password }); await setSession(session.access_token, session.user); router.replace("/(tabs)"); }
    catch (reason) { setError(getApiErrorMessage(reason)); } finally { setLoading(false); }
  };
  return <Screen><View style={styles.header}><Text style={styles.title}>Create your energy workspace</Text><Text style={styles.copy}>Use the same account on the web dashboard and mobile app.</Text></View><View style={styles.form}><AppInput label="Full name" value={name} onChangeText={setName} autoComplete="name" /><AppInput label="Email" value={email} onChangeText={setEmail} keyboardType="email-address" autoCapitalize="none" autoComplete="email" /><AppInput label="Password" value={password} onChangeText={setPassword} secureTextEntry autoComplete="new-password" />{error ? <Text style={styles.error}>{error}</Text> : null}<AppButton label="Create account" onPress={submit} loading={loading} /><Text style={styles.linkCopy}>Already registered? <Link href="/(auth)/login" style={styles.link}>Sign in</Link></Text></View></Screen>;
}

const styles = StyleSheet.create({ header: { marginTop: 34, gap: 10 }, title: { color: colors.text, fontSize: 34, lineHeight: 40, fontWeight: "800" }, copy: { color: colors.textMuted, lineHeight: 22 }, form: { marginTop: 18, gap: 15 }, error: { color: colors.danger }, linkCopy: { color: colors.textMuted, textAlign: "center" }, link: { color: colors.primary, fontWeight: "700" } });
