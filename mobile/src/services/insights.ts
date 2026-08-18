import { apiClient } from "@/lib/apiClient";

export const insightService = {
  anomalies: async (householdId: string, deviceId: string, limit = 30) =>
    (await apiClient.get(`/households/${householdId}/devices/${deviceId}/anomalies`, { params: { limit } })).data,
  recommendations: async (householdId: string) =>
    (await apiClient.get(`/recommendations/${householdId}`)).data,
  forecast: async (householdId: string, days = 30) =>
    (await apiClient.get(`/forecast/${householdId}`, { params: { days } })).data,
};
