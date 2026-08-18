import { useEffect } from "react";
import { authService } from "@/services/auth";
import { tokenStorage } from "@/lib/tokenStorage";
import { useAuthStore } from "@/store/authStore";

export function useSessionRestore() {
  const { setUser, finishRestore } = useAuthStore();

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const token = await tokenStorage.get();
        if (token) {
          const user = await authService.me();
          if (mounted) setUser(user);
        }
      } catch {
        await tokenStorage.clear();
      } finally {
        if (mounted) finishRestore();
      }
    })();
    return () => { mounted = false; };
  }, [finishRestore, setUser]);
}
