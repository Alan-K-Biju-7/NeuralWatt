import { useLiveWatt } from "../hooks/useLiveWatt";
import { Activity, Clock3, Radio, Zap } from "lucide-react";
import {
  LineChart, Line, ResponsiveContainer, Tooltip, YAxis
} from "recharts";

export default function LiveWattCard({ householdId, deviceName }) {
  const { watts, history, connected, secondsAgo, trend } = useLiveWatt(householdId);

  const trendLabel = trend.charAt(0).toUpperCase() + trend.slice(1);
  const trendClass = trend === "rising"
    ? "text-orange-300 bg-orange-500/10 border-orange-500/20"
    : trend === "falling"
    ? "text-emerald-300 bg-emerald-500/10 border-emerald-500/20"
    : "text-slate-300 bg-slate-800 border-slate-700";

  return (
    <section className="overflow-hidden rounded-lg border border-slate-800 bg-slate-900/80 shadow-xl shadow-black/20">
      <div className="flex flex-col gap-4 border-b border-slate-800 px-5 py-4 md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-teal-500/10 text-teal-300">
            <Zap className="h-5 w-5" />
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Live load</p>
            <h2 className="text-base font-semibold text-white">{deviceName || "Selected device"}</h2>
          </div>
        </div>
        <div className={`inline-flex w-fit items-center gap-2 rounded-full border px-3 py-1 text-xs font-medium ${
          connected
            ? "border-emerald-500/20 bg-emerald-500/10 text-emerald-300"
            : "border-red-500/20 bg-red-500/10 text-red-300"
        }`}>
          <span className={`h-2 w-2 rounded-full ${connected ? "bg-emerald-400" : "bg-red-400"}`} />
          {connected ? "Connected" : "Reconnecting"}
        </div>
      </div>

      <div className="grid min-h-[230px] grid-cols-1 lg:grid-cols-[360px_1fr]">
        <div className="flex flex-col justify-between border-b border-slate-800 p-5 lg:border-b-0 lg:border-r">
          <div>
            <p className="text-sm text-slate-500">Current demand</p>
            <div className="mt-3 flex items-end gap-2">
              <span className="text-5xl font-semibold tracking-tight text-white sm:text-6xl">
                {watts !== null ? watts.toFixed(1) : "—"}
              </span>
              <span className="pb-2 text-xl font-medium text-slate-500">W</span>
            </div>
          </div>
          <div className="mt-6 grid grid-cols-2 gap-3">
            <div className={`rounded-lg border px-3 py-2 ${trendClass}`}>
              <div className="flex items-center gap-2 text-xs font-medium">
                <Activity className="h-3.5 w-3.5" />
                {trendLabel}
              </div>
            </div>
            <div className="rounded-lg border border-slate-800 bg-slate-950/50 px-3 py-2 text-slate-300">
              <div className="flex items-center gap-2 text-xs font-medium">
                <Clock3 className="h-3.5 w-3.5 text-slate-500" />
                {secondsAgo !== null ? `${secondsAgo}s ago` : "Waiting"}
              </div>
            </div>
          </div>
        </div>

        <div className="flex min-h-[210px] flex-col p-5">
          <div className="mb-4 flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm font-medium text-slate-300">
              <Radio className="h-4 w-4 text-teal-300" />
              Recent signal
            </div>
            <span className="text-xs text-slate-500">{history.length} samples</span>
          </div>

          {history.length > 1 ? (
            <div className="min-h-[130px] flex-1">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={history} margin={{ top: 6, right: 8, bottom: 0, left: 8 }}>
                  <YAxis domain={["auto", "auto"]} hide />
                  <Tooltip
                    formatter={(v) => [`${v.toFixed(1)} W`, "Watts"]}
                    contentStyle={{
                      background: "#0f172a",
                      border: "1px solid #1e293b",
                      borderRadius: "8px",
                      color: "#e2e8f0",
                      fontSize: "12px",
                    }}
                    labelStyle={{ color: "#94a3b8" }}
                  />
                  <Line
                    type="monotone"
                    dataKey="watts"
                    stroke="#2dd4bf"
                    strokeWidth={3}
                    dot={false}
                    isAnimationActive={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="flex min-h-[130px] flex-1 items-center justify-center rounded-lg border border-dashed border-slate-800 bg-slate-950/40 text-sm text-slate-500">
              Waiting for readings
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
