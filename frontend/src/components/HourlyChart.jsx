import { useQuery } from "@tanstack/react-query";
import { analyticsAPI } from "../lib/api";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer
} from "recharts";
import { Clock } from "lucide-react";

const fmt24 = (h) => {
  const suffix = h >= 12 ? "PM" : "AM";
  const hour   = h % 12 || 12;
  return `${hour}${suffix}`;
};

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-slate-800 border border-slate-600 rounded-xl p-3 shadow-xl text-sm">
      <p className="text-slate-300 font-medium mb-2">{fmt24(label)}</p>
      <p className="text-teal-400">
        <span className="text-slate-400">Avg: </span>
        {payload[0]?.value?.toFixed(1)} W
      </p>
      <p className="text-orange-400">
        <span className="text-slate-400">Peak: </span>
        {payload[0]?.payload?.peak_watts} W
      </p>
      <p className="text-slate-500">
        {payload[0]?.payload?.reading_count} readings
      </p>
    </div>
  );
};

export default function HourlyChart({ householdId, deviceId, days = 7 }) {
  const { data, isLoading } = useQuery({
    queryKey:        ["hourly-chart", deviceId, days],
    enabled:         !!deviceId && !!householdId,
    queryFn:         () => analyticsAPI.hourly(householdId, deviceId, days).then(r => r.data),
    refetchInterval: 120000,
  });

  // Fill all 24 hours so chart is never gappy
  const chartData = Array.from({ length: 24 }, (_, h) => {
    const found = data?.hours?.find(x => x.hour === h);
    return found ?? { hour: h, avg_watts: 0, peak_watts: 0, reading_count: 0 };
  });

  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900/80 p-5 shadow-lg shadow-black/10">
      <div className="flex items-center justify-between mb-5">
        <div>
          <h3 className="text-white font-semibold flex items-center gap-2">
            <Clock className="w-4 h-4 text-teal-400" />
            Hourly Pattern
          </h3>
          <p className="text-slate-500 text-xs mt-0.5">Last {days} days · avg watts/hour</p>
        </div>
        {data && (
          <div className="text-right">
            <p className="text-orange-400 font-bold text-lg">
              {fmt24(data.peak_hour)}
            </p>
            <p className="text-slate-500 text-xs">Peak hour</p>
          </div>
        )}
      </div>

      {isLoading ? (
        <div className="h-48 flex items-center justify-center">
          <div className="w-8 h-8 border-2 border-teal-500 border-t-transparent
                          rounded-full animate-spin" />
        </div>
      ) : !data?.hours?.length ? (
        <div className="h-48 flex flex-col items-center justify-center text-slate-500">
          <Clock className="w-10 h-10 mb-2 opacity-30" />
          <p className="text-sm">No hourly data yet</p>
          <p className="text-xs mt-1">Need readings across different hours</p>
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={200}>
          <AreaChart data={chartData} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="tealGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%"  stopColor="#14b8a6" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#14b8a6" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
            <XAxis
              dataKey="hour"
              tickFormatter={fmt24}
              tick={{ fill: "#94a3b8", fontSize: 10 }}
              axisLine={false}
              tickLine={false}
              interval={3}
            />
            <YAxis
              tick={{ fill: "#94a3b8", fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(v) => `${v}W`}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ stroke: "#475569" }} />
            <Area
              type="monotone"
              dataKey="avg_watts"
              stroke="#14b8a6"
              strokeWidth={2}
              fill="url(#tealGrad)"
              dot={false}
              activeDot={{ r: 4, fill: "#14b8a6", stroke: "#0f172a", strokeWidth: 2 }}
            />
          </AreaChart>
        </ResponsiveContainer>
      )}

      {/* Peak + low summary */}
      {data?.hours?.length > 0 && (
        <div className="grid grid-cols-2 gap-3 mt-4 pt-4 border-t border-slate-800">
          <div className="bg-slate-950/40 rounded-lg border border-slate-800 p-3 text-center">
            <p className="text-orange-400 font-bold">{fmt24(data.peak_hour)}</p>
            <p className="text-slate-400 text-xs mt-0.5">Peak hour</p>
            <p className="text-slate-300 text-xs">{data.peak_hour_avg_watts?.toFixed(1)} W avg</p>
          </div>
          <div className="bg-slate-950/40 rounded-lg border border-slate-800 p-3 text-center">
            <p className="text-teal-400 font-bold">{data.hours.length} hrs</p>
            <p className="text-slate-400 text-xs mt-0.5">Active hours</p>
            <p className="text-slate-300 text-xs">last {days} days</p>
          </div>
        </div>
      )}
    </div>
  );
}
