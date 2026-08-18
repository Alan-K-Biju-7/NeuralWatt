import { apiClient } from "@/lib/apiClient";
import type { AuthResponse, LoginInput, RegisterInput, User } from "@/types/auth";

export const authService = {
  login: async (input: LoginInput) => (await apiClient.post<AuthResponse>("/auth/login", input)).data,
  register: async (input: RegisterInput) => (await apiClient.post<AuthResponse>("/auth/register", input)).data,
  me: async () => (await apiClient.get<User>("/auth/me")).data,
};
