import { apiClient } from "@/lib/apiClient";
import type { Device, Household } from "@/types/household";

export const householdService = {
  mine: async () => (await apiClient.get<Household>("/households/me")).data,
  devices: async (householdId: string) =>
    (await apiClient.get<Device[]>(`/households/${householdId}/devices`)).data,
};
