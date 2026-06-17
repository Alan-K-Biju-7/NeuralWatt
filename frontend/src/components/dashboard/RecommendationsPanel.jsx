import { useQuery } from "@tanstack/react-query";
import {
  AlertTriangle,
  BadgeCheck,
  BarChart3,
  IndianRupee,
  Lightbulb,
  Zap,
} from "lucide-react";
import { recommendationAPI } from "../../lib/api";

const PRIORITY_STYLE = {
  high: {
    wrap: "border-red-500/25 bg-red-500/10",
    badge: "bg-red-500/15 text-red-200",
    icon: Zap,
    iconWrap: "bg-red-500/15 text-red-300",
  },
  medium: {
    wrap: "border-amber-500/25 bg-amber-500/10",
    badge: "bg-amber-500/15 text-amber-200",
    icon: BarChart3,
    iconWrap: "bg-amber-500/15 text-amber-300",
  },
  low: {
    wrap: "border-teal-500/25 bg-teal-500/10",
    badge: "bg-teal-500/15 text-teal-200",
    icon: BadgeCheck,
    iconWrap: "bg-teal-500/15 text-teal-300",
  },
  info: {
    wrap: "border-slate-700 bg-slate-800/50",
    badge: "bg-slate-700 text-slate-300",
    icon: BadgeCheck,
    iconWrap: "bg-slate-700 text-slate-300",
  },
};

const monthlySavingsFor = (item, summary) => {
  if (typeof item.estimated_saving_inr === "number") return item.estimated_saving_inr;

  const dailyCost = summary?.estimated_daily_cost || 0;
  const monthlyCost = dailyCost * 30;
  const priority = item.priority || item.severity || "info";
  if (priority === "high") return monthlyCost * 0.12;
  if (priority === "medium") return monthlyCost * 0.05;
  return 0;
};

const descriptionFor = (item) => item.description || item.message || item.savings_hint;

function LoadingCards() {
  return (
    <div className="space-y-3">
      {[0, 1, 2].map((index) => (
        <div key={index} className="h-24 animate-pulse rounded-lg bg-slate-800" />
      ))}
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
  const totalEstimatedSaving =
    data?.total_estimated_saving_inr ??
    recommendations.reduce(
      (total, item) => total + monthlySavingsFor(item, summary),
      0
    );

  return (
    <div className="space-y-3">
      <div className="rounded-lg border border-slate-800 bg-slate-900/80 p-5 shadow-lg shadow-black/10">
        <div className="mb-5 flex items-start justify-between gap-4">
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
            {recommendations.length} active
          </span>
        </div>

        {isLoading ? (
          <LoadingCards />
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
            {totalEstimatedSaving > 0 && (
              <div className="mb-4 flex items-center justify-between rounded-lg border border-emerald-500/25 bg-emerald-500/10 px-4 py-3">
                <span className="text-sm font-medium text-emerald-200">
                  Potential monthly savings
                </span>
                <span className="flex items-center gap-1 text-lg font-bold text-emerald-200">
                  <IndianRupee className="h-4 w-4" />
                  {totalEstimatedSaving.toFixed(0)}
                </span>
              </div>
            )}

            <div className="space-y-3">
              {recommendations.map((item) => (
                <RecommendationCard
                  key={item.id || item.title}
                  item={item}
                  summary={summary}
                />
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function RecommendationCard({ item, summary }) {
  const priority = item.priority || item.severity || "info";
  const style = PRIORITY_STYLE[priority] || PRIORITY_STYLE.info;
  const Icon = style.icon;
  const estimatedSaving = monthlySavingsFor(item, summary);

  return (
    <div className={`rounded-lg border p-4 ${style.wrap}`}>
      <div className="flex items-start gap-3">
        <span
          className={`mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${style.iconWrap}`}
        >
          <Icon className="h-4 w-4" />
        </span>
        <div className="min-w-0 flex-1">
          <div className="mb-1 flex flex-wrap items-center justify-between gap-2">
            <p className="text-sm font-semibold text-white">{item.title}</p>
            <div className="flex flex-wrap items-center gap-2">
              <span
                className={`rounded-full px-2 py-0.5 text-[11px] font-bold uppercase tracking-wide ${style.badge}`}
              >
                {priority}
              </span>
              {estimatedSaving > 0 && (
                <span
                  className={`flex items-center gap-0.5 rounded-full px-2 py-0.5 text-xs font-semibold ${style.badge}`}
                >
                  <IndianRupee className="h-3 w-3" />
                  {estimatedSaving.toFixed(0)}/mo
                </span>
              )}
            </div>
          </div>
          <p className="text-xs leading-relaxed text-slate-300">
            {descriptionFor(item)}
          </p>
          {item.savings_hint && item.savings_hint !== descriptionFor(item) && (
            <p className="mt-2 text-xs text-slate-400">{item.savings_hint}</p>
          )}
        </div>
      </div>
    </div>
  );
}
