import { useQuery } from "@tanstack/react-query";
import { analyticsAPI, anomalyAPI } from "../lib/api";
import { Zap, IndianRupee, AlertTriangle, TrendingUp, Activity } from "lucide-react";

function KPICard({ title, value, sub, icon: Icon, color, loading }) {
  return (
    <div className="bg-slate-800 border border-slate-700 rounded-2xl p-5">
      <div className="flex items-start justify-between mb-4">
        <p className="text-slate-400 text-sm font-medium">{title}</p>
        <div className={`w-9 h-9 rounded-xl flex items-center justify-center ${color}`}>
          <Icon className="w-4 h-4 text-white" />
        </div>
      </div>
      {loading ? (
        <div className="h-8 w-24 bg-slate-700 rounded animate-pulse" />
      ) : (
        <p className="text-white text-2xl font-bold tracking-tight">{value}</p>
      )}
      <p className="text-slate-500 text-xs mt-1">{sub}</p>
    </div>
  );
}

function SlabBreakdown({ slabs, fixed, duty, meter, total }) {
  return (
    <div className="bg-slate-800 border border-slate-700 rounded-2xl p-5 col-span-full">
      <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
        <IndianRupee className="w-4 h-4 text-teal-400" />
        KSEB Bill Breakdown
      </h3>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-slate-400 border-b border-slate-700">
              <th className="text-left pb-2 font-medium">Slab</th>
              <th className="text-right pb-2 font-medium">Units (kWh)</th>
              <th className="text-right pb-2 font-medium">Rate (₹/kWh)</th>
              <th className="text-right pb-2 font-medium">Amount (₹)</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700/50">
            {slabs?.map((s, i) => (
              <tr key={i} className="text-slate-300">
                <td className="py-2">{s.slab_label}</td>
                <td className="py-2 text-right tabular-nums">{s.units.toFixed(3)}</td>
                <td className="py-2 text-right tabular-nums">₹{s.rate_per_unit.toFixed(2)}</td>
                <td className="py-2 text-right tabular-nums">₹{s.slab_cost.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
          <tfoot className="border-t border-slate-600">
            <tr className="text-slate-400 text-xs">
              <td colSpan={3} className="pt-3">Fixed charge</td>
              <td className="pt-3 text-right tabular-nums">₹{fixed?.toFixed(2)}</td>
            </tr>
            <tr className="text-slate-400 text-xs">
              <td colSpan={3}>Electricity duty (10%)</td>
              <td className="text-right tabular-nums">₹{duty?.toFixed(2)}</td>
            </tr>
            <tr className="text-slate-400 text-xs">
              <td colSpan={3}>Meter rent</td>
              <td className="text-right tabular-nums">₹{meter?.toFixed(2)}</td>
            </tr>
            <tr className="text-white font-bold">
              <td colSpan={3} className="pt-2">Total Bill</td>
              <td className="pt-2 text-right tabular-nums text-teal-400">
                ₹{total?.toFixed(2)}
              </td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  );
}

export default function KPICards({ householdId, deviceId, costOnly = false }) {
  const { data: daily, isLoading: loadDaily } = useQuery({
    queryKey:  ["daily", deviceId],
    enabled:   !!deviceId && !!householdId,
    queryFn:   () => analyticsAPI.daily(householdId, deviceId, 30).then(r => r.data),
    refetchInterval: 60000,
  });

  const { data: cost, isLoading: loadCost } = useQuery({
    queryKey:  ["cost", deviceId],
    enabled:   !!deviceId && !!householdId,
    queryFn:   () => analyticsAPI.cost(householdId, deviceId, 30).then(r => r.data),
    refetchInterval: 60000,
  });

  const { data: report, isLoading: loadReport } = useQuery({
    queryKey:  ["report", deviceId],
    enabled:   !!deviceId && !!householdId && !costOnly,
    queryFn:   () => analyticsAPI.report(householdId, deviceId, "monthly").then(r => r.data),
    refetchInterval: 60000,
  });

  const { data: baseline } = useQuery({
    queryKey:  ["baseline", deviceId],
    enabled:   !!deviceId && !!householdId && !costOnly,
    queryFn:   () => anomalyAPI.baseline(householdId, deviceId).then(r => r.data),
  });

  if (costOnly) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <KPICard
          title="Total kWh (30 days)"
          value={`${daily?.total_kwh?.toFixed(2) ?? "—"} kWh`}
          sub="Pro-rated for KSEB calculation"
          icon={Zap}
          color="bg-teal-500"
          loading={loadDaily}
        />
        <KPICard
          title="Energy Charge"
          value={`₹${cost?.energy_charge?.toFixed(2) ?? "—"}`}
          sub="Before duty & fixed charge"
          icon={IndianRupee}
          color="bg-blue-500"
          loading={loadCost}
        />
        <KPICard
          title="Electricity Duty"
          value={`₹${cost?.electricity_duty?.toFixed(2) ?? "—"}`}
          sub="10% on energy charge"
          icon={TrendingUp}
          color="bg-orange-500"
          loading={loadCost}
        />
        <KPICard
          title="Estimated Bill"
          value={`₹${cost?.total_bill?.toFixed(2) ?? "—"}`}
          sub="KSEB LT-1 Telescopic Tariff"
          icon={IndianRupee}
          color="bg-purple-500"
          loading={loadCost}
        />
        <SlabBreakdown
          slabs={cost?.slab_breakdown}
          fixed={cost?.fixed_charge}
          duty={cost?.electricity_duty}
          meter={cost?.meter_rent}
          total={cost?.total_bill}
        />
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
      <KPICard
        title="Total Usage (30d)"
        value={`${daily?.total_kwh?.toFixed(3) ?? "—"} kWh`}
        sub={`${daily?.days?.length ?? 0} days of data`}
        icon={Zap}
        color="bg-teal-500"
        loading={loadDaily}
      />
      <KPICard
        title="Est. KSEB Bill"
        value={`₹${cost?.total_bill?.toFixed(2) ?? "—"}`}
        sub="LT-1 Telescopic · 30 days"
        icon={IndianRupee}
        color="bg-green-500"
        loading={loadCost}
      />
      <KPICard
        title="Anomalies (month)"
        value={report?.anomaly_count ?? "—"}
        sub="HIGH / MEDIUM / LOW events"
        icon={AlertTriangle}
        color="bg-red-500"
        loading={loadReport}
      />
      <KPICard
        title="Baseline Avg"
        value={baseline ? `${baseline.avg_watts?.toFixed(1)} W` : "—"}
        sub={baseline ? `±${baseline.std_dev?.toFixed(1)}W · ${baseline.sample_count} samples` : "Need 3+ readings"}
        icon={Activity}
        color="bg-blue-500"
        loading={false}
      />
    </div>
  );
}
