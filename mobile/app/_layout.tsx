import { QueryClientProvider } from "@tanstack/react-query";
import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { queryClient } from "@/lib/queryClient";
import { useSessionRestore } from "@/hooks/useSessionRestore";
import { colors } from "@/theme/colors";

function Navigation() {
  useSessionRestore();
  return <><StatusBar style="light" /><Stack screenOptions={{ headerShown: false, contentStyle: { backgroundColor: colors.background } }} /></>;
}

export default function RootLayout() {
  return <QueryClientProvider client={queryClient}><Navigation /></QueryClientProvider>;
}
