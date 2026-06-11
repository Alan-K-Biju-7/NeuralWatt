import { useQuery } from "@tanstack/react-query";
import { anomalyAPI } from "../lib/api";
import { AlertTriangle, BellRing, ShieldCheck, Zap } from "lucide-react";

const SEVERITY = {
  high: {
    bg: "bg-red-500/10",
    border: "border-red-500/30",
    text: "text-red-400",
    badge: "bg-red-500/20 text-red-400",
    dot: "bg-red-400",
    icon: AlertTriangle,
  },
  medium: {
    bg: "bg-orange-500/10",
    border: "border-orange-500/30",
    text: "text-orange-400",
    badge: "bg-orange-500/20 text-orange-400",
    dot: "bg-orange-400",
    icon: Zap,
  },
  low: {
    bg: "bg-yellow-500/10",
    border: "border-yellow-500/30",
    text: "text-yellow-400",
    badge: "bg-yellow-500/20 text-yellow-400",
    dot: "bg-yellow-400",
    icon: Zap,
  },
  info: {
    bg: "bg-slate-500/10",
    border: "border-slate-500/30",
    text: "text-slate-300",
    badge: "bg-slate-500/20 text-slate-300",
    dot: "bg-slate-400",
    icon: BellRing,
  },
};

const fmtTime = (iso) => {
  if (!iso) return "-";
  const d = new Date(iso);
  return d.toLocaleString("en-IN", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
    hour12: true,
  });
};

export default function AnomalyFeed({ householdId, limit = 15 }) {
  const { data, isLoading } = useQuery({
    queryKey: ["triggered-alerts", householdId, limit],
    enabled: !!householdId,
    queryFn: () =>
      anomalyAPI.triggeredAlerts(householdId, limit).then((r) => r.data),
    refetchInterval: 30000,
  });

  const alerts = data?.triggered_alerts || [];

  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900/80 p-5 shadow-lg shadow-black/10">
      <div className="flex items-center justify-between mb-5">
        <div>
          <h3 className="text-white font-semibold flex items-center gap-2">
            <BellRing className="w-4 h-4 text-red-400" />
            Triggered Alerts
          </h3>
          <p className="text-slate-500 text-xs mt-0.5">
            Recent alert-rule matches · auto-refreshes every 30s
          </p>
        </div>
        {data && (
          <span className="bg-red-500/15 text-red-400 text-xs font-semibold px-3 py-1 rounded-full border border-red-500/20">
            {data.count} recent
          </span>
        )}
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-16 bg-slate-800 rounded-lg animate-pulse" />
          ))}
        </div>
      ) : alerts.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12 text-slate-500">
          <ShieldCheck className="w-12 h-12 mb-3 text-teal-500/40" />
          <p className="text-sm font-medium text-slate-400">No alerts triggered recently</p>
          <p className="text-xs mt-1">Configured alert rules will appear here when matched</p>
        </div>
      ) : (
        <div className="space-y-3">
          {alerts.map((alert) => {
            const severity = alert.severity || "info";
            const s = SEVERITY[severity] || SEVERITY.info;
            const Icon = s.icon;
            return (
              <div
                key={alert.id}
                className={`${s.bg} ${s.border} border rounded-lg p-4 flex items-start gap-3`}
              >
                <div className={`${s.badge} w-8 h-8 rounded-lg flex items-center justify-center shrink-0 mt-0.5`}>
                  <Icon className="w-4 h-4" />
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className={`${s.dot} h-2 w-2 rounded-full`} />
                    <span className={`${s.badge} text-xs font-bold px-2 py-0.5 rounded-full uppercase tracking-wider`}>
                      {severity}
                    </span>
                    <span className="text-slate-400 text-xs">
                      {fmtTime(alert.timestamp)}
                    </span>
                  </div>
                  <p className={`${s.text} text-sm font-medium mt-1`}>
                    {alert.reason || alert.message || "Alert rule matched"}
                  </p>
                  <p className="text-slate-400 text-xs mt-0.5">
                    {alert.watts?.toLocaleString("en-IN") ?? "-"} W detected
                    {alert.expected_watts != null && (
                      <> · expected ~{Number(alert.expected_watts).toFixed(1)} W</>
                    )}
                  </p>
                </div>

                <div className="text-right shrink-0">
                  <p className="text-white text-sm font-bold tabular-nums">
                    {alert.channels?.join(", ") || "alert"}
                  </p>
                  <p className="text-slate-500 text-xs">channel</p>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
