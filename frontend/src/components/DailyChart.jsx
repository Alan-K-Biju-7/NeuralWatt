import { useQuery } from "@tanstack/react-query";
import { analyticsAPI } from "../lib/api";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Cell
} from "recharts";
import { BarChart2 } from "lucide-react";

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-slate-800 border border-slate-600 rounded-xl p-3 shadow-xl text-sm">
      <p className="text-slate-300 font-medium mb-2">{label}</p>
      <p className="text-teal-400">
        <span className="text-slate-400">Usage: </span>
        {payload[0]?.value?.toFixed(4)} kWh
      </p>
      <p className="text-orange-400">
        <span className="text-slate-400">Peak: </span>
        {payload[0]?.payload?.peak_watts} W
      </p>
      <p className="text-blue-400">
        <span className="text-slate-400">Avg: </span>
        {payload[0]?.payload?.avg_watts} W
      </p>
      <p className="text-slate-500">
        {payload[0]?.payload?.reading_count} readings
      </p>
    </div>
  );
};

export default function DailyChart({ householdId, deviceId, days = 30 }) {
  const { data, isLoading } = useQuery({
    queryKey:        ["daily-chart", deviceId, days],
    enabled:         !!deviceId && !!householdId,
    queryFn:         () => analyticsAPI.daily(householdId, deviceId, days).then(r => r.data),
    refetchInterval: 120000,
  });

  const chartData = data?.days?.map(d => ({
    ...d,
    dateShort: d.date.slice(5),   // "05-11"
  })) || [];

  const maxKwh = Math.max(...chartData.map(d => d.kwh), 0.001);

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-2xl p-5">
      <div className="flex items-center justify-between mb-5">
        <div>
          <h3 className="text-white font-semibold flex items-center gap-2">
            <BarChart2 className="w-4 h-4 text-teal-400" />
            Daily Usage
          </h3>
          <p className="text-slate-500 text-xs mt-0.5">Last {days} days · kWh</p>
        </div>
        <div className="text-right">
          <p className="text-teal-400 font-bold text-lg">
            {data?.total_kwh?.toFixed(3) ?? "—"} kWh
          </p>
          <p className="text-slate-500 text-xs">Total</p>
        </div>
      </div>

      {isLoading ? (
        <div className="h-48 flex items-center justify-center">
          <div className="w-8 h-8 border-2 border-teal-500 border-t-transparent
                          rounded-full animate-spin" />
        </div>
      ) : chartData.length === 0 ? (
        <div className="h-48 flex flex-col items-center justify-center text-slate-500">
          <BarChart2 className="w-10 h-10 mb-2 opacity-30" />
          <p className="text-sm">No usage data yet</p>
          <p className="text-xs mt-1">Post some readings to see your daily chart</p>
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={chartData} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
            <XAxis
              dataKey="dateShort"
              tick={{ fill: "#94a3b8", fontSize: 11 }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              tick={{ fill: "#94a3b8", fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(v) => `${v}`}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: "#1e293b" }} />
            <Bar dataKey="kwh" radius={[4, 4, 0, 0]} maxBarSize={48}>
              {chartData.map((entry, i) => (
                <Cell
                  key={i}
                  fill={entry.kwh === maxKwh ? "#f97316" : "#14b8a6"}
                  fillOpacity={0.85}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      )}

      {/* Summary row */}
      {data && (
        <div className="grid grid-cols-3 gap-2 mt-4 pt-4 border-t border-slate-700">
          {[
            { label: "From",  value: data.from_date },
            { label: "Days",  value: data.days.length },
            { label: "To",    value: data.to_date },
          ].map(({ label, value }) => (
            <div key={label} className="text-center">
              <p className="text-white text-sm font-medium">{value}</p>
              <p className="text-slate-500 text-xs">{label}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
