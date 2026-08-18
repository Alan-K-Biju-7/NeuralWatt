import { useEffect, useState } from "react";
import { openLiveReadings } from "@/services/liveReadings";

type LivePayload = { power_w?: number; watts?: number; type?: string };

export function useLivePower(householdId?: string, initialPower = 0) {
  const [power, setPower] = useState(initialPower);
  const [connected, setConnected] = useState(false);

  useEffect(() => setPower(initialPower), [initialPower]);
  useEffect(() => {
    if (!householdId) return;
    const socket = openLiveReadings(householdId, (raw) => {
      const payload = raw as LivePayload;
      const next = payload.power_w ?? payload.watts;
      if (typeof next === "number") setPower(next);
    });
    socket.onopen = () => setConnected(true);
    socket.onclose = () => setConnected(false);
    return () => socket.close();
  }, [householdId]);

  return { power, connected };
}
