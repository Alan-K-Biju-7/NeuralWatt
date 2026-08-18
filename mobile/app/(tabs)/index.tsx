import { useQuery } from "@tanstack/react-query";
import { StyleSheet, Text, View } from "react-native";
import { EmptyState } from "@/components/EmptyState";
import { EnergyCard } from "@/components/EnergyCard";
import { ErrorState } from "@/components/ErrorState";
import { LoadingState } from "@/components/LoadingState";
import { Metric } from "@/components/Metric";
import { Screen } from "@/components/Screen";
import { useHousehold } from "@/hooks/useHousehold";
import { useLivePower } from "@/hooks/useLivePower";
import { analyticsService } from "@/services/analytics";
import { colors } from "@/theme/colors";

export default function OverviewScreen() {
  const householdQuery = useHousehold(); const { household, device } = householdQuery;
  const summary = useQuery({ queryKey: ["summary", household?.id, device?.id], queryFn: () => analyticsService.summary(household!.id, device!.id), enabled: Boolean(household && device), refetchInterval: 60_000 });
  const live = useLivePower(household?.id, summary.data?.live_power_w ?? 0);
  if (householdQuery.isLoading) return <LoadingState />;
  if (householdQuery.error) return <Screen><ErrorState message="Check the API address and try again." retry={() => householdQuery.refetch()} /></Screen>;
  if (!household || !device) return <Screen><EmptyState title="No energy device yet" message="Add a household meter from the web dashboard to begin monitoring." /></Screen>;
  return <Screen><View style={styles.heading}><Text style={styles.kicker}>{household.name}</Text><Text style={styles.title}>Energy overview</Text><Text style={styles.device}>{device.name} · {live.connected ? "Live" : "Reconnecting"}</Text></View><EnergyCard><Text style={styles.liveLabel}>Power right now</Text><Text style={styles.liveValue}>{Math.round(live.power).toLocaleString()} <Text style={styles.unit}>W</Text></Text><View style={[styles.dot, live.connected ? styles.online : styles.offline]} /></EnergyCard>{summary.isLoading ? <LoadingState label="Calculating today’s usage…" /> : summary.error ? <ErrorState message="Summary data is temporarily unavailable." retry={() => summary.refetch()} /> : <EnergyCard title="Today"><View style={styles.metrics}><Metric label="Energy" value={`${summary.data?.today_kwh.toFixed(2) ?? "0.00"} kWh`} accent /><Metric label="Average" value={`${Math.round(summary.data?.avg_power_w ?? 0)} W`} /><Metric label="Peak" value={`${Math.round(summary.data?.peak_power_w ?? 0)} W`} /><Metric label="Anomalies" value={`${summary.data?.anomaly_count ?? 0}`} /></View></EnergyCard>}</Screen>;
}

const styles = StyleSheet.create({ heading: { gap: 5 }, kicker: { color: colors.primary, fontWeight: "700" }, title: { color: colors.text, fontSize: 31, fontWeight: "800" }, device: { color: colors.textMuted }, liveLabel: { color: colors.textMuted }, liveValue: { color: colors.text, fontSize: 50, fontWeight: "900" }, unit: { color: colors.primary, fontSize: 22 }, dot: { position: "absolute", right: 18, top: 18, width: 10, height: 10, borderRadius: 5 }, online: { backgroundColor: colors.primary }, offline: { backgroundColor: colors.warning }, metrics: { flexDirection: "row", flexWrap: "wrap", rowGap: 18 } });
