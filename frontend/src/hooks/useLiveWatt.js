import { useState, useEffect, useRef, useCallback } from "react";
import { IS_DEMO } from "../lib/api";

const WS_BASE = "ws://localhost:8000";
const MAX_HISTORY = 20;
const RECONNECT_DELAY = 3000;

export function useLiveWatt(householdId, deviceId) {
  const [watts, setWatts]         = useState(null);
  const [history, setHistory]     = useState([]);
  const [connected, setConnected] = useState(false);
  const [lastSeen, setLastSeen]   = useState(null);
  const wsRef                     = useRef(null);
  const retryRef                  = useRef(null);

  const connect = useCallback(() => {
    if (!householdId) return;

    if (IS_DEMO) {
      setConnected(true);
      const addReading = () => {
        const value = Number((510 + Math.sin(Date.now() / 8000) * 135).toFixed(1));
        const timestamp = new Date().toISOString();
        setWatts(value);
        setLastSeen(new Date());
        setHistory((previous) => [...previous, { watts: value, timestamp }].slice(-MAX_HISTORY));
      };
      addReading();
      retryRef.current = window.setInterval(addReading, 3000);
      return;
    }

    const url = `${WS_BASE}/ws/readings/${householdId}`;
    const socket = new WebSocket(url);
    wsRef.current = socket;

    socket.onopen = () => {
      setConnected(true);
    };

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === "ping") return;
      if (data.type === "reading") {
        if (deviceId && data.device_id !== deviceId) return;
        setWatts(data.watts);
        setLastSeen(new Date());
        setHistory((prev) => {
          const next = [...prev, { watts: data.watts, timestamp: data.timestamp }];
          return next.slice(-MAX_HISTORY);
        });
      }
    };

    socket.onclose = () => {
      setConnected(false);
      // Auto-reconnect after 3s
      retryRef.current = setTimeout(connect, RECONNECT_DELAY);
    };

    socket.onerror = () => {
      socket.close();
    };
  }, [householdId, deviceId]);

  useEffect(() => {
    connect();
    return () => {
      IS_DEMO ? clearInterval(retryRef.current) : clearTimeout(retryRef.current);
      wsRef.current?.close();
    };
  }, [connect]);

  useEffect(() => {
    setWatts(null);
    setHistory([]);
    setLastSeen(null);
  }, [deviceId]);

  // How many seconds since last reading
  const secondsAgo = lastSeen
    ? Math.floor((Date.now() - lastSeen.getTime()) / 1000)
    : null;

  // Simple trend — compare last 2 readings
  const trend = history.length >= 2
    ? history[history.length - 1].watts > history[history.length - 2].watts
      ? "rising" : "falling"
    : "stable";

  return { watts, history, connected, secondsAgo, trend };
}
