import { useQuery } from "@tanstack/react-query";
import { StyleSheet, Text, View } from "react-native";
import { EnergyCard } from "@/components/EnergyCard";
import { ErrorState } from "@/components/ErrorState";
import { LoadingState } from "@/components/LoadingState";
import { Screen } from "@/components/Screen";
import { useHousehold } from "@/hooks/useHousehold";
import { insightService } from "@/services/insights";
import { colors } from "@/theme/colors";

export default function InsightsScreen() {
  const { household, isLoading } = useHousehold();
  const query = useQuery({ queryKey: ["recommendations", household?.id], queryFn: () => insightService.recommendations(household!.id), enabled: Boolean(household) });
  if (isLoading || query.isLoading) return <LoadingState label="Finding useful energy insights…" />;
  if (query.error) return <Screen><ErrorState message="Recommendations are temporarily unavailable." retry={() => query.refetch()} /></Screen>;
  return <Screen><View style={styles.header}><Text style={styles.title}>Smart insights</Text><Text style={styles.copy}>Practical suggestions based on the latest 24 hours.</Text></View>{query.data?.recommendations.map((item) => <EnergyCard key={item.id} title={item.title}><Text style={styles.message}>{item.message}</Text><View style={styles.hint}><Text style={styles.hintText}>{item.savings_hint}</Text></View></EnergyCard>)}</Screen>;
}

const styles = StyleSheet.create({ header: { gap: 6 }, title: { color: colors.text, fontSize: 31, fontWeight: "800" }, copy: { color: colors.textMuted }, message: { color: colors.text, lineHeight: 22 }, hint: { alignSelf: "flex-start", borderRadius: 10, backgroundColor: colors.surfaceRaised, paddingVertical: 7, paddingHorizontal: 10 }, hintText: { color: colors.primary, fontSize: 12, fontWeight: "700" } });
