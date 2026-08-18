import { create } from "zustand";
import type { User } from "@/types/auth";
import { tokenStorage } from "@/lib/tokenStorage";

type AuthState = {
  user: User | null;
  isRestoring: boolean;
  setSession: (token: string, user: User) => Promise<void>;
  setUser: (user: User | null) => void;
  finishRestore: () => void;
  signOut: () => Promise<void>;
};

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isRestoring: true,
  setSession: async (token, user) => {
    await tokenStorage.set(token);
    set({ user });
  },
  setUser: (user) => set({ user }),
  finishRestore: () => set({ isRestoring: false }),
  signOut: async () => {
    await tokenStorage.clear();
    set({ user: null });
  },
}));
