import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  BarChart3,
  Bell,
  CheckCircle2,
  Cpu,
  Mail,
  Save,
  Settings as SettingsIcon,
  Webhook,
} from "lucide-react";
import { alertAPI, nilmAPI } from "../../lib/api";

const DEFAULT_FORM = {
  severity_threshold: "high",
  email_enabled: false,
  email_address: "",
  webhook_enabled: false,
  webhook_url: "",
};

function Metric({ label, value }) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-950/50 p-4">
      <p className="text-xs text-slate-500">{label}</p>
      <p className="mt-1 text-xl font-bold text-white">{value}</p>
    </div>
  );
}

const importanceScore = (item) => item.mean_abs_shap ?? item.importance ?? 0;

function FeatureImportanceBars({ isLoading, rows }) {
  if (isLoading && !rows.length) {
    return <div className="h-36 animate-pulse rounded-lg bg-slate-800" />;
  }

  if (!rows.length) {
    return (
      <div className="rounded-lg border border-slate-800 bg-slate-950/50 p-4 text-sm text-slate-500">
        Feature importance is not available yet.
      </div>
    );
  }

  const maxScore = Math.max(...rows.map(importanceScore), 0) || 1;

  return (
    <div className="space-y-2">
      {rows.slice(0, 8).map((item) => {
        const score = importanceScore(item);
        const width = Math.max(8, Math.min(100, Math.round((score / maxScore) * 100)));

        return (
          <div key={item.feature}>
            <div className="mb-1 flex items-center justify-between gap-3 text-xs">
              <span className="truncate text-slate-400">{item.feature}</span>
              <span className="shrink-0 font-medium text-slate-300">
                {score.toFixed(4)}
              </span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-slate-800">
              <div
                className="h-full rounded-full bg-sky-400"
                style={{ width: `${width}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}

export default function Settings({ householdId, deviceId }) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState(DEFAULT_FORM);
  const [saved, setSaved] = useState(false);

  const { data: modelCard, isLoading: modelLoading } = useQuery({
    queryKey: ["nilm-model-card"],
    queryFn: () => nilmAPI.modelCard(),
  });

  const { data: shapImportance, isLoading: shapLoading } = useQuery({
    queryKey: ["nilm-shap-importance"],
    queryFn: () => nilmAPI.shapImportance(),
    retry: false,
  });

  const { data: alertConfig, isLoading: configLoading } = useQuery({
    queryKey: ["alert-config", householdId, deviceId],
    enabled: !!householdId && !!deviceId,
    queryFn: async () => {
      try {
        const { data } = await alertAPI.get(householdId, deviceId);
        return data;
      } catch (error) {
        if (error.response?.status === 404) return null;
        throw error;
      }
    },
  });

  useEffect(() => {
    if (!alertConfig) return;
    setForm({
      severity_threshold: alertConfig.severity_threshold || "high",
      email_enabled: Boolean(alertConfig.email_enabled),
      email_address: alertConfig.email_address || "",
      webhook_enabled: Boolean(alertConfig.webhook_enabled),
      webhook_url: alertConfig.webhook_url || "",
    });
  }, [alertConfig]);

  const canSave = useMemo(() => {
    if (form.email_enabled && !form.email_address.trim()) return false;
    if (form.webhook_enabled && !form.webhook_url.trim()) return false;
    return form.email_enabled || form.webhook_enabled;
  }, [form]);

  const mutation = useMutation({
    mutationFn: async () => {
      const payload = {
        severity_threshold: form.severity_threshold,
        email_enabled: form.email_enabled,
        email_address: form.email_enabled ? form.email_address.trim() : null,
        webhook_enabled: form.webhook_enabled,
        webhook_url: form.webhook_enabled ? form.webhook_url.trim() : null,
      };
      if (alertConfig?.id) {
        const { data } = await alertAPI.update(householdId, deviceId, payload);
        return data;
      }
      const { data } = await alertAPI.create(householdId, deviceId, payload);
      return data;
    },
    onSuccess: () => {
      setSaved(true);
      queryClient.invalidateQueries({ queryKey: ["alert-config", householdId, deviceId] });
      window.setTimeout(() => setSaved(false), 1800);
    },
  });

  const updateField = (field, value) => {
    setForm((current) => ({ ...current, [field]: value }));
  };

  const featureImportance = useMemo(() => {
    if (shapImportance?.feature_importance?.length) {
      return shapImportance.feature_importance;
    }
    return modelCard?.top_feature_importance || [];
  }, [modelCard?.top_feature_importance, shapImportance?.feature_importance]);

  const importanceSource =
    shapImportance?.source === "shap" ? "SHAP" : "Model fallback";

  return (
    <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1fr_1.1fr]">
      <div className="rounded-lg border border-slate-800 bg-slate-900/80 p-5 shadow-lg shadow-black/10">
        <div className="mb-5 flex items-center justify-between gap-4">
          <div>
            <h3 className="flex items-center gap-2 font-semibold text-white">
              <Bell className="h-4 w-4 text-teal-400" />
              Alert Settings
            </h3>
            <p className="mt-0.5 text-xs text-slate-500">
              Device alert delivery and severity threshold
            </p>
          </div>
          {saved && (
            <span className="flex items-center gap-1 rounded-full bg-teal-500/10 px-3 py-1 text-xs font-semibold text-teal-300">
              <CheckCircle2 className="h-3 w-3" />
              Saved
            </span>
          )}
        </div>

        {configLoading ? (
          <div className="h-64 animate-pulse rounded-lg bg-slate-800" />
        ) : (
          <div className="space-y-5">
            <label className="block">
              <span className="mb-2 block text-sm font-medium text-slate-300">
                Minimum severity
              </span>
              <select
                value={form.severity_threshold}
                onChange={(event) => updateField("severity_threshold", event.target.value)}
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-3 text-sm text-white outline-none focus:border-teal-400"
              >
                <option value="high">High only</option>
                <option value="medium">Medium and high</option>
                <option value="low">Low, medium, and high</option>
              </select>
            </label>

            <div className="rounded-lg border border-slate-800 bg-slate-950/50 p-4">
              <label className="flex items-center justify-between gap-3">
                <span className="flex items-center gap-2 text-sm font-medium text-slate-200">
                  <Mail className="h-4 w-4 text-blue-300" />
                  Email alerts
                </span>
                <input
                  type="checkbox"
                  checked={form.email_enabled}
                  onChange={(event) => updateField("email_enabled", event.target.checked)}
                  className="h-4 w-4 accent-teal-500"
                />
              </label>
              {form.email_enabled && (
                <input
                  type="email"
                  value={form.email_address}
                  onChange={(event) => updateField("email_address", event.target.value)}
                  placeholder="alerts@example.com"
                  className="mt-3 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-3 text-sm text-white outline-none focus:border-teal-400"
                />
              )}
            </div>

            <div className="rounded-lg border border-slate-800 bg-slate-950/50 p-4">
              <label className="flex items-center justify-between gap-3">
                <span className="flex items-center gap-2 text-sm font-medium text-slate-200">
                  <Webhook className="h-4 w-4 text-purple-300" />
                  Webhook alerts
                </span>
                <input
                  type="checkbox"
                  checked={form.webhook_enabled}
                  onChange={(event) => updateField("webhook_enabled", event.target.checked)}
                  className="h-4 w-4 accent-teal-500"
                />
              </label>
              {form.webhook_enabled && (
                <input
                  type="url"
                  value={form.webhook_url}
                  onChange={(event) => updateField("webhook_url", event.target.value)}
                  placeholder="https://example.com/energy-alerts"
                  className="mt-3 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-3 text-sm text-white outline-none focus:border-teal-400"
                />
              )}
            </div>

            <button
              type="button"
              onClick={() => mutation.mutate()}
              disabled={!canSave || mutation.isPending}
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-teal-500 px-4 py-3 text-sm font-semibold text-white transition-colors hover:bg-teal-400 disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-400"
            >
              <Save className="h-4 w-4" />
              {mutation.isPending ? "Saving" : "Save alert settings"}
            </button>

            {mutation.error && (
              <p className="text-sm text-red-300">
                {mutation.error.response?.data?.detail || "Could not save alert settings."}
              </p>
            )}
            {!canSave && (
              <p className="text-xs text-slate-500">
                Enable email or webhook alerts and provide the required address.
              </p>
            )}
          </div>
        )}
      </div>

      <div className="rounded-lg border border-slate-800 bg-slate-900/80 p-5 shadow-lg shadow-black/10">
        <div className="mb-5 flex items-center justify-between gap-4">
          <div>
            <h3 className="flex items-center gap-2 font-semibold text-white">
              <Cpu className="h-4 w-4 text-teal-400" />
              NILM Model Card
            </h3>
            <p className="mt-0.5 text-xs text-slate-500">
              Current trained appliance classifier
            </p>
          </div>
          <SettingsIcon className="h-4 w-4 text-slate-500" />
        </div>

        {modelLoading ? (
          <div className="h-64 animate-pulse rounded-lg bg-slate-800" />
        ) : !modelCard ? (
          <div className="flex h-64 items-center justify-center text-sm text-slate-500">
            Model metadata unavailable
          </div>
        ) : (
          <div className="space-y-5">
            <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
              <Metric label="Classes" value={modelCard.n_classes ?? "-"} />
              <Metric
                label="Test accuracy"
                value={
                  modelCard.test_accuracy != null
                    ? `${(modelCard.test_accuracy * 100).toFixed(2)}%`
                    : "-"
                }
              />
              <Metric
                label="CV mean"
                value={
                  modelCard.cv_mean_accuracy != null
                    ? `${(modelCard.cv_mean_accuracy * 100).toFixed(2)}%`
                    : "-"
                }
              />
              <Metric label="Windows" value={modelCard.total_feature_windows ?? "-"} />
            </div>

            <div>
              <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
                Appliance classes
              </p>
              <div className="flex flex-wrap gap-2">
                {modelCard.classes?.map((name) => (
                  <span
                    key={name}
                    className="rounded-full border border-slate-700 bg-slate-800 px-3 py-1 text-xs text-slate-300"
                  >
                    {name.replaceAll("_", " ")}
                  </span>
                ))}
              </div>
            </div>

            <div>
              <div className="mb-2 flex items-center justify-between gap-3">
                <p className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
                  <BarChart3 className="h-3.5 w-3.5 text-sky-300" />
                  Feature Importance (SHAP)
                </p>
                <span className="rounded-full border border-slate-700 bg-slate-800 px-2 py-0.5 text-[11px] font-semibold text-slate-300">
                  {importanceSource}
                </span>
              </div>
              <FeatureImportanceBars
                isLoading={shapLoading}
                rows={featureImportance}
              />
              {shapImportance?.message && (
                <p className="mt-2 text-xs text-slate-500">{shapImportance.message}</p>
              )}
            </div>

            <p className="rounded-lg border border-slate-800 bg-slate-950/50 p-4 text-sm text-slate-400">
              {modelCard.limitation}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
