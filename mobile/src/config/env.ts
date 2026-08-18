import Constants from "expo-constants";

type MobileExtra = { apiUrl?: string; wsUrl?: string };

const extra = (Constants.expoConfig?.extra ?? {}) as MobileExtra;

export const env = {
  apiUrl: process.env.EXPO_PUBLIC_API_URL ?? extra.apiUrl ?? "http://localhost:8000/api/v1",
  wsUrl: process.env.EXPO_PUBLIC_WS_URL ?? extra.wsUrl ?? "ws://localhost:8000/ws",
};
