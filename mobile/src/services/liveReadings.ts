import { env } from "@/config/env";

export function openLiveReadings(householdId: string, onMessage: (payload: unknown) => void) {
  const socket = new WebSocket(`${env.wsUrl}/${householdId}`);
  socket.onmessage = (event) => {
    try {
      onMessage(JSON.parse(event.data));
    } catch {
      // Ignore malformed frames while keeping the live stream connected.
    }
  };
  return socket;
}
