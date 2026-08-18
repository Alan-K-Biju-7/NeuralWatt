import { useQuery } from "@tanstack/react-query";
import { StyleSheet, Text, View } from "react-native";
import { EnergyCard } from "@/components/EnergyCard";
import { ErrorState } from "@/components/ErrorState";
import { LoadingState } from "@/components/LoadingState";
import { Metric } from "@/components/Metric";
import { Screen } from "@/components/Screen";
import { useHousehold } from "@/hooks/useHousehold";
import { analyticsService } from "@/services/analytics";
import { colors } from "@/theme/colors";

export default function AnalyticsScreen() {
  const { household, device, isLoading } = useHousehold();
  const daily = useQuery({ queryKey: ["daily", household?.id, device?.id], queryFn: () => analyticsService.daily(household!.id, device!.id), enabled: Boolean(household && device) });
  const cost = useQuery({ queryKey: ["cost", household?.id, device?.id], queryFn: () => analyticsService.cost(household!.id, device!.id), enabled: Boolean(household && device) });
  if (isLoading || daily.isLoading || cost.isLoading) return <LoadingState label="Building your usage view…" />;
  if (daily.error || cost.error) return <Screen><ErrorState message="Usage analytics are temporarily unavailable." retry={() => { daily.refetch(); cost.refetch(); }} /></Screen>;
  return <Screen><Text style={styles.title}>Usage and cost</Text><EnergyCard title="Last 30 days"><View style={styles.metrics}><Metric label="Energy" value={`${daily.data?.total_kwh.toFixed(2) ?? "0.00"} kWh`} accent /><Metric label="Estimated bill" value={`₹${cost.data?.total_bill.toFixed(0) ?? "0"}`} /></View></EnergyCard><EnergyCard title="Daily energy">{daily.data?.days.slice(-10).reverse().map((point) => { const width = `${Math.min(100, point.kwh / Math.max(...(daily.data?.days.map((item) => item.kwh) ?? [1])) * 100)}%` as `${number}%`; return <View key={point.date} style={styles.row}><Text style={styles.date}>{point.date.slice(5)}</Text><View style={styles.track}><View style={[styles.bar, { width }]} /></View><Text style={styles.value}>{point.kwh.toFixed(2)}</Text></View>; })}</EnergyCard></Screen>;
}

const styles = StyleSheet.create({ title: { color: colors.text, fontSize: 31, fontWeight: "800" }, metrics: { flexDirection: "row", gap: 18 }, row: { flexDirection: "row", alignItems: "center", gap: 9 }, date: { width: 43, color: colors.textMuted, fontSize: 12 }, track: { flex: 1, height: 9, borderRadius: 5, backgroundColor: colors.surfaceRaised, overflow: "hidden" }, bar: { height: 9, borderRadius: 5, backgroundColor: colors.primary }, value: { width: 38, color: colors.text, fontSize: 12, textAlign: "right" } });
