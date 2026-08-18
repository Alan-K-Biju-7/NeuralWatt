import axios from "axios";
import { env } from "@/config/env";
import { tokenStorage } from "@/lib/tokenStorage";

export const apiClient = axios.create({
  baseURL: env.apiUrl,
  timeout: 15_000,
  headers: { "Content-Type": "application/json" },
});

apiClient.interceptors.request.use(async (config) => {
  const token = await tokenStorage.get();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export function getApiErrorMessage(error: unknown) {
  if (axios.isAxiosError(error)) {
    return error.response?.data?.detail ?? error.message ?? "Unable to reach NeuralWatt";
  }
  return error instanceof Error ? error.message : "Something went wrong";
}
