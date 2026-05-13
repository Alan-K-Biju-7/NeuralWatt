import { useLiveWatt } from "../hooks/useLiveWatt";
import {
  LineChart, Line, ResponsiveContainer, Tooltip, YAxis
} from "recharts";

export default function LiveWattCard({ householdId }) {
  const { watts, history, connected, secondsAgo, trend } = useLiveWatt(householdId);

  const trendIcon = trend === "rising" ? "↑" : trend === "falling" ? "↓" : "→";
  const trendColor = trend === "rising"
    ? "#f59e0b"
    : trend === "falling"
    ? "#10b981"
    : "#6b7280";

  return (
    <div style={{
      background: "#1e1e2e",
      border: "1px solid #2a2a3e",
      borderRadius: "16px",
      padding: "24px",
      minWidth: "280px",
      color: "#fff",
      fontFamily: "sans-serif",
    }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
        <span style={{ fontSize: "13px", fontWeight: 600, letterSpacing: "0.1em", color: "#a0a0b0" }}>
          ⚡ LIVE
        </span>
        <span style={{
          fontSize: "11px",
          padding: "3px 10px",
          borderRadius: "999px",
          background: connected ? "#10b98122" : "#ef444422",
          color: connected ? "#10b981" : "#ef4444",
          fontWeight: 600,
        }}>
          {connected ? "🟢 Connected" : "🔴 Reconnecting..."}
        </span>
      </div>

      {/* Watts Display */}
      <div style={{ textAlign: "center", margin: "16px 0" }}>
        <span style={{ fontSize: "56px", fontWeight: 700, letterSpacing: "-2px", color: "#fff" }}>
          {watts !== null ? watts.toFixed(1) : "—"}
        </span>
        <span style={{ fontSize: "20px", color: "#a0a0b0", marginLeft: "6px" }}>W</span>
      </div>

      {/* Trend + Last seen */}
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "20px", fontSize: "13px" }}>
        <span style={{ color: trendColor, fontWeight: 600 }}>
          {trendIcon} {trend.charAt(0).toUpperCase() + trend.slice(1)}
        </span>
        <span style={{ color: "#a0a0b0" }}>
          {secondsAgo !== null ? `Last: ${secondsAgo}s ago` : "Waiting..."}
        </span>
      </div>

      {/* Sparkline */}
      {history.length > 1 && (
        <ResponsiveContainer width="100%" height={60}>
          <LineChart data={history}>
            <YAxis domain={["auto", "auto"]} hide />
            <Tooltip
              formatter={(v) => [`${v.toFixed(1)} W`, "Watts"]}
              contentStyle={{ background: "#2a2a3e", border: "none", borderRadius: "8px", fontSize: "12px" }}
            />
            <Line
              type="monotone"
              dataKey="watts"
              stroke="#6366f1"
              strokeWidth={2}
              dot={false}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      )}

      {history.length <= 1 && (
        <div style={{ textAlign: "center", color: "#a0a0b0", fontSize: "12px", marginTop: "8px" }}>
          Waiting for readings...
        </div>
      )}
    </div>
  );
}
