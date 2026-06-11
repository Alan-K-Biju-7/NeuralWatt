import { useQuery } from "@tanstack/react-query";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { TrendingUp } from "lucide-react";
import { forecastAPI } from "../../lib/api";

const formatHour = (iso) =>
  new Date(iso).toLocaleTimeString("en-IN", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: true,
  });

function TooltipContent({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  const point = payload[0].payload;
  return (
    <div className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm shadow-xl">
      <p className="mb-1 font-medium text-slate-200">{formatHour(label)}</p>
      <p className="text-teal-300">
        Forecast: {point.predicted_kwh.toFixed(4)} kWh
      </p>
      <p className="text-slate-400">
        Range: {point.lower_kwh.toFixed(4)} - {point.upper_kwh.toFixed(4)} kWh
      </p>
    </div>
  );
}

export default function ForecastChart({ householdId }) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["forecast", householdId],
    enabled: !!householdId,
    queryFn: () => forecastAPI.get(householdId, 30),
    refetchInterval: 10 * 60 * 1000,
  });

  const points = data?.forecast || [];
  const total = points.reduce((sum, point) => sum + point.predicted_kwh, 0);

  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900/80 p-5 shadow-lg shadow-black/10">
      <div className="mb-5 flex items-center justify-between gap-4">
        <div>
          <h3 className="flex items-center gap-2 font-semibold text-white">
            <TrendingUp className="h-4 w-4 text-teal-400" />
            24 Hour Forecast
          </h3>
          <p className="mt-0.5 text-xs text-slate-500">
            Prophet demand forecast · household total
          </p>
        </div>
        <div className="text-right">
          <p className="text-lg font-bold text-teal-300">
            {points.length ? `${total.toFixed(3)} kWh` : "-"}
          </p>
          <p className="text-xs text-slate-500">Projected</p>
        </div>
      </div>

      {isLoading ? (
        <div className="flex h-72 items-center justify-center">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-teal-500 border-t-transparent" />
        </div>
      ) : error ? (
        <div className="flex h-72 flex-col items-center justify-center text-center">
          <TrendingUp className="mb-3 h-10 w-10 text-slate-700" />
          <p className="text-sm font-medium text-slate-300">Forecast unavailable</p>
          <p className="mt-1 max-w-md text-xs text-slate-500">
            {error.response?.data?.detail || "More hourly history is needed before a forecast can be trained."}
          </p>
        </div>
      ) : points.length === 0 ? (
        <div className="flex h-72 items-center justify-center text-sm text-slate-500">
          No forecast points available
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={points} margin={{ top: 10, right: 12, left: -18, bottom: 0 }}>
            <CartesianGrid stroke="#334155" strokeDasharray="3 3" vertical={false} />
            <XAxis
              dataKey="hour"
              tickFormatter={formatHour}
              axisLine={false}
              tickLine={false}
              tick={{ fill: "#94a3b8", fontSize: 11 }}
            />
            <YAxis
              axisLine={false}
              tickLine={false}
              tick={{ fill: "#94a3b8", fontSize: 11 }}
              tickFormatter={(value) => value.toFixed(2)}
            />
            <Tooltip content={<TooltipContent />} />
            <Area
              type="monotone"
              dataKey="upper_kwh"
              stroke="transparent"
              fill="#14b8a6"
              fillOpacity={0.12}
            />
            <Area
              type="monotone"
              dataKey="predicted_kwh"
              stroke="#2dd4bf"
              strokeWidth={2}
              fill="#14b8a6"
              fillOpacity={0.28}
            />
          </AreaChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
