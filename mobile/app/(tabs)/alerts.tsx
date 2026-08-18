import { useQuery } from "@tanstack/react-query";
import { StyleSheet, Text, View } from "react-native";
import { EmptyState } from "@/components/EmptyState";
import { EnergyCard } from "@/components/EnergyCard";
import { ErrorState } from "@/components/ErrorState";
import { LoadingState } from "@/components/LoadingState";
import { Screen } from "@/components/Screen";
import { useHousehold } from "@/hooks/useHousehold";
import { insightService } from "@/services/insights";
import { colors } from "@/theme/colors";

export default function AlertsScreen() {
  const { household, device, isLoading } = useHousehold();
  const query = useQuery({ queryKey: ["anomalies", household?.id, device?.id], queryFn: () => insightService.anomalies(household!.id, device!.id), enabled: Boolean(household && device) });
  if (isLoading || query.isLoading) return <LoadingState label="Checking unusual energy activity…" />;
  if (query.error) return <Screen><ErrorState message="Alerts are temporarily unavailable." retry={() => query.refetch()} /></Screen>;
  return <Screen><Text style={styles.title}>Energy alerts</Text>{query.data?.anomalies.length ? query.data.anomalies.map((item) => <EnergyCard key={item.id}><View style={styles.row}><View style={[styles.badge, item.severity === "high" && styles.high]}><Text style={styles.badgeText}>{item.severity.toUpperCase()}</Text></View><Text style={styles.time}>{new Date(item.detected_at).toLocaleString()}</Text></View><Text style={styles.message}>{item.message}</Text><Text style={styles.detail}>{Math.round(item.watts)} W · {Math.round(item.deviation_pct)}% from baseline</Text></EnergyCard>) : <EmptyState title="No unusual activity" message="NeuralWatt has not detected any recent power anomalies." />}</Screen>;
}

const styles = StyleSheet.create({ title: { color: colors.text, fontSize: 31, fontWeight: "800" }, row: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" }, badge: { borderRadius: 8, paddingHorizontal: 8, paddingVertical: 4, backgroundColor: colors.warning }, high: { backgroundColor: colors.danger }, badgeText: { color: colors.background, fontSize: 10, fontWeight: "900" }, time: { color: colors.textMuted, fontSize: 11 }, message: { color: colors.text, lineHeight: 21 }, detail: { color: colors.textMuted, fontSize: 12 } });
