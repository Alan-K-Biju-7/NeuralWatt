import { create } from "zustand";
import { authAPI } from "../lib/api";

const useAuthStore = create((set) => ({
  user:          null,
  token:         localStorage.getItem("nw_token") || null,
  isLoading:     false,
  error:         null,

  login: async (email, password) => {
    set({ isLoading: true, error: null });
    try {
      const form = new URLSearchParams();
      form.append("username", email);
      form.append("password", password);
      const { data } = await authAPI.login(form);
      localStorage.setItem("nw_token", data.access_token);
      set({ token: data.access_token, isLoading: false });
      return true;
    } catch (err) {
      set({ error: err.response?.data?.detail || "Login failed", isLoading: false });
      return false;
    }
  },

  register: async (name, email, password) => {
    set({ isLoading: true, error: null });
    try {
      await authAPI.register({ name, email, password });
      set({ isLoading: false });
      return true;
    } catch (err) {
      set({ error: err.response?.data?.detail || "Registration failed", isLoading: false });
      return false;
    }
  },

  fetchUser: async () => {
    try {
      const { data } = await authAPI.me();
      set({ user: data });
    } catch {
      set({ user: null });
    }
  },

  logout: () => {
    localStorage.removeItem("nw_token");
    set({ user: null, token: null, error: null });
    window.location.href = "/login";
  },

  clearError: () => set({ error: null }),
}));

export default useAuthStore;
