import { apiClient } from "@/lib/apiClient";
import type { CostEstimate, DailyUsage, HourlyUsage } from "@/types/analytics";

export type Summary = {
  live_power_w: number;
  today_kwh: number;
  avg_power_w: number;
  peak_power_w: number;
  projected_monthly_kwh: number;
  anomaly_count: number;
};

export const analyticsService = {
  summary: async (householdId: string, deviceId: string) =>
    (await apiClient.get<Summary>(`/households/${householdId}/devices/${deviceId}/analytics/summary`)).data,
  daily: async (householdId: string, deviceId: string, days = 30) =>
    (await apiClient.get<DailyUsage>(`/households/${householdId}/devices/${deviceId}/analytics/daily`, { params: { days } })).data,
  hourly: async (householdId: string, deviceId: string, days = 7) =>
    (await apiClient.get<HourlyUsage>(`/households/${householdId}/devices/${deviceId}/analytics/hourly`, { params: { days } })).data,
  cost: async (householdId: string, deviceId: string, days = 30) =>
    (await apiClient.get<CostEstimate>(`/households/${householdId}/devices/${deviceId}/analytics/cost`, { params: { days } })).data,
};
