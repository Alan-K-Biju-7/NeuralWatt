import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, IndianRupee, Lightbulb, ShieldCheck, Zap } from "lucide-react";
import { recommendationAPI } from "../../lib/api";

const SEVERITY_STYLE = {
  high: "border-red-500/30 bg-red-500/10 text-red-300",
  medium: "border-orange-500/30 bg-orange-500/10 text-orange-300",
  low: "border-teal-500/30 bg-teal-500/10 text-teal-300",
};

function SummaryTile({ icon: Icon, label, value }) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-950/50 p-4">
      <div className="mb-3 flex h-9 w-9 items-center justify-center rounded-lg bg-slate-800 text-teal-300">
        <Icon className="h-4 w-4" />
      </div>
      <p className="text-xl font-bold text-white">{value}</p>
      <p className="mt-1 text-xs text-slate-500">{label}</p>
    </div>
  );
}

export default function RecommendationsPanel({ householdId }) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["recommendations", householdId],
    enabled: !!householdId,
    queryFn: () => recommendationAPI.get(householdId),
    refetchInterval: 2 * 60 * 1000,
  });

  const summary = data?.summary;
  const recommendations = data?.recommendations || [];

  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-slate-800 bg-slate-900/80 p-5 shadow-lg shadow-black/10">
        <div className="mb-5 flex items-center justify-between gap-4">
          <div>
            <h3 className="flex items-center gap-2 font-semibold text-white">
              <Lightbulb className="h-4 w-4 text-yellow-300" />
              Smart Recommendations
            </h3>
            <p className="mt-0.5 text-xs text-slate-500">
              Latest 24-hour household pattern
            </p>
          </div>
          <span className="rounded-full border border-slate-700 bg-slate-800 px-3 py-1 text-xs font-semibold text-slate-300">
            {recommendations.length || 0} active
          </span>
        </div>

        {isLoading ? (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            {[...Array(3)].map((_, index) => (
              <div key={index} className="h-28 animate-pulse rounded-lg bg-slate-800" />
            ))}
          </div>
        ) : error ? (
          <div className="flex h-40 flex-col items-center justify-center text-center">
            <AlertTriangle className="mb-3 h-10 w-10 text-slate-700" />
            <p className="text-sm font-medium text-slate-300">Recommendations unavailable</p>
            <p className="mt-1 text-xs text-slate-500">
              {error.response?.data?.detail || "Could not load recommendation rules."}
            </p>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <SummaryTile
                icon={Zap}
                label="Energy in 24h"
                value={`${summary?.total_kwh?.toFixed(3) ?? "0.000"} kWh`}
              />
              <SummaryTile
                icon={IndianRupee}
                label="Estimated daily cost"
                value={`₹${summary?.estimated_daily_cost?.toFixed(2) ?? "0.00"}`}
              />
              <SummaryTile
                icon={ShieldCheck}
                label="Peak-window energy"
                value={`${summary?.peak_kwh?.toFixed(3) ?? "0.000"} kWh`}
              />
            </div>

            <div className="mt-5 space-y-3">
              {recommendations.map((item) => (
                <div
                  key={item.id}
                  className={`rounded-lg border p-4 ${
                    SEVERITY_STYLE[item.severity] || SEVERITY_STYLE.low
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <Lightbulb className="mt-0.5 h-4 w-4 shrink-0" />
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <p className="font-semibold text-white">{item.title}</p>
                        <span className="rounded-full bg-slate-950/40 px-2 py-0.5 text-[11px] font-bold uppercase tracking-wide">
                          {item.severity}
                        </span>
                      </div>
                      <p className="mt-1 text-sm text-slate-300">{item.message}</p>
                      <p className="mt-2 text-xs text-slate-400">{item.savings_hint}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
