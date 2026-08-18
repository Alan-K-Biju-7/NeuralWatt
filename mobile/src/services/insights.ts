import { apiClient } from "@/lib/apiClient";
import type { AnomalyResponse, ForecastResponse, RecommendationResponse } from "@/types/insights";

export const insightService = {
  anomalies: async (householdId: string, deviceId: string, limit = 30) =>
    (await apiClient.get<AnomalyResponse>(`/households/${householdId}/devices/${deviceId}/anomalies`, { params: { limit } })).data,
  recommendations: async (householdId: string) =>
    (await apiClient.get<RecommendationResponse>(`/recommendations/${householdId}`)).data,
  forecast: async (householdId: string, days = 30) =>
    (await apiClient.get<ForecastResponse>(`/forecast/${householdId}`, { params: { days } })).data,
};
