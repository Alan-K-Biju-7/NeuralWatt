import { useQuery } from "@tanstack/react-query";
import { anomalyAPI } from "../lib/api";
import { AlertTriangle, ShieldCheck, Zap } from "lucide-react";

const SEVERITY = {
  high:   { bg: "bg-red-500/10",    border: "border-red-500/30",    text: "text-red-400",    badge: "bg-red-500/20 text-red-400",    icon: AlertTriangle },
  medium: { bg: "bg-orange-500/10", border: "border-orange-500/30", text: "text-orange-400", badge: "bg-orange-500/20 text-orange-400", icon: Zap },
  low:    { bg: "bg-yellow-500/10", border: "border-yellow-500/30", text: "text-yellow-400", badge: "bg-yellow-500/20 text-yellow-400", icon: Zap },
};

const fmtTime = (iso) => {
  const d = new Date(iso);
  return d.toLocaleString("en-IN", {
    day: "2-digit", month: "short",
    hour: "2-digit", minute: "2-digit",
    hour12: true,
  });
};

export default function AnomalyFeed({ householdId, deviceId, limit = 10 }) {
  const { data, isLoading } = useQuery({
    queryKey:        ["anomalies", deviceId, limit],
    enabled:         !!deviceId && !!householdId,
    queryFn:         () =>
      anomalyAPI.list(householdId, deviceId, { limit }).then(r => r.data),
    refetchInterval: 30000,    // refresh every 30s
  });

  const anomalies = data?.anomalies || [];

  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900/80 p-5 shadow-lg shadow-black/10">
      <div className="flex items-center justify-between mb-5">
        <div>
          <h3 className="text-white font-semibold flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-red-400" />
            Anomaly Feed
          </h3>
          <p className="text-slate-500 text-xs mt-0.5">
            Auto-refreshes every 30s
          </p>
        </div>
        {data && (
          <span className="bg-red-500/15 text-red-400 text-xs font-semibold
                           px-3 py-1 rounded-full border border-red-500/20">
            {data.total} total
          </span>
        )}
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-16 bg-slate-800 rounded-lg animate-pulse" />
          ))}
        </div>
      ) : anomalies.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12 text-slate-500">
          <ShieldCheck className="w-12 h-12 mb-3 text-teal-500/40" />
          <p className="text-sm font-medium text-slate-400">All clear!</p>
          <p className="text-xs mt-1">No anomalies detected for this device</p>
        </div>
      ) : (
        <div className="space-y-3">
          {anomalies.map((a) => {
            const s = SEVERITY[a.severity] || SEVERITY.low;
            const Icon = s.icon;
            return (
              <div
                key={a.id}
                className={`${s.bg} ${s.border} border rounded-lg p-4
                            flex items-start gap-3`}
              >
                <div className={`${s.badge} w-8 h-8 rounded-lg flex items-center
                                 justify-center shrink-0 mt-0.5`}>
                  <Icon className="w-4 h-4" />
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className={`${s.badge} text-xs font-bold px-2 py-0.5
                                      rounded-full uppercase tracking-wider`}>
                      {a.severity}
                    </span>
                    <span className="text-slate-400 text-xs">
                      {fmtTime(a.detected_at)}
                    </span>
                  </div>
                  <p className={`${s.text} text-sm font-medium mt-1`}>
                    {a.watts.toLocaleString("en-IN")} W detected
                  </p>
                  <p className="text-slate-400 text-xs mt-0.5">
                    Expected ~{a.expected_watts.toFixed(1)} W ·{" "}
                    <span className={s.text}>
                      {a.deviation_pct > 0 ? "+" : ""}
                      {a.deviation_pct.toFixed(1)}% deviation
                    </span>
                  </p>
                </div>

                <div className="text-right shrink-0">
                  <p className="text-white text-sm font-bold tabular-nums">
                    {a.watts.toLocaleString("en-IN")} W
                  </p>
                  <p className="text-slate-500 text-xs">actual</p>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
