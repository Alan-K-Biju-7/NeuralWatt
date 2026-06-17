import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useQuery } from "@tanstack/react-query";
import { forecastAPI } from "../../lib/api";

const formatHour = (iso) =>
  new Date(iso).toLocaleTimeString("en-IN", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: true,
  });

export default function ForecastChart({ householdId }) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["forecast", householdId],
    enabled: !!householdId,
    queryFn: () => forecastAPI.get(householdId, 30),
    refetchInterval: 10 * 60 * 1000,
  });

  if (isLoading) {
    return <div className="h-56 animate-pulse rounded-lg bg-slate-800/70" />;
  }

  if (error) {
    return (
      <div className="flex h-56 items-center justify-center rounded-lg border border-dashed border-slate-700 text-sm text-slate-500">
        {error.response?.data?.detail ||
          "More hourly history is needed before a forecast can be trained."}
      </div>
    );
  }

  const chartData = (data?.forecast || []).map((point) => ({
    hour: point.hour,
    label: formatHour(point.hour),
    kWh: point.predicted_kwh,
    upper: point.upper_kwh,
  }));
  const total = chartData.reduce((sum, point) => sum + point.kWh, 0);
  const peakPoint = chartData.reduce(
    (peak, point) => (!peak || point.kWh > peak.kWh ? point : peak),
    null
  );

  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900/80 p-5 shadow-lg shadow-black/10">
      <div className="mb-3 flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            24 Hour Forecast
          </p>
          <p className="mt-0.5 text-2xl font-bold text-white">
            {chartData.length ? total.toFixed(3) : "-"}{" "}
            <span className="text-base font-normal text-slate-500">kWh</span>
          </p>
        </div>
        <div className="text-right text-xs text-slate-500">
          <p>Peak at</p>
          <p className="font-semibold text-slate-200">
            {peakPoint ? peakPoint.label : "-"}
          </p>
        </div>
      </div>

      {chartData.length === 0 ? (
        <div className="flex h-56 items-center justify-center text-sm text-slate-500">
          No forecast points available
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={200}>
          <AreaChart
            data={chartData}
            margin={{ top: 4, right: 8, left: -18, bottom: 0 }}
          >
            <defs>
              <linearGradient id="forecastGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.22} />
                <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="#1e293b" strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="label" tick={{ fill: "#94a3b8", fontSize: 10 }} interval={3} />
            <YAxis tick={{ fill: "#94a3b8", fontSize: 10 }} tickFormatter={(value) => value.toFixed(2)} />
            <Tooltip formatter={(value) => [`${value} kWh`]} labelStyle={{ fontSize: 11 }} />
            <Area
              type="monotone"
              dataKey="kWh"
              stroke="#0ea5e9"
              strokeWidth={2}
              fill="url(#forecastGradient)"
              dot={false}
              name="Predicted"
            />
            <Area
              type="monotone"
              dataKey="upper"
              stroke="#64748b"
              strokeWidth={1}
              strokeDasharray="4 4"
              fill="none"
              dot={false}
              name="Upper bound"
            />
          </AreaChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
