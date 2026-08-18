import { Redirect } from "expo-router";
import { LoadingState } from "@/components/LoadingState";
import { useAuthStore } from "@/store/authStore";

export default function Index() {
  const { user, isRestoring } = useAuthStore();
  if (isRestoring) return <LoadingState label="Restoring your NeuralWatt session…" />;
  return <Redirect href={user ? "/(tabs)" : "/(auth)/login"} />;
}
