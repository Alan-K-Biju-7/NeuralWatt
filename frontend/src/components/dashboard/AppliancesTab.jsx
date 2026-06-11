import { useEffect, useState } from "react";
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { nilmAPI } from "../../lib/api";

const COLORS = [
  "#0ea5e9",
  "#22c55e",
  "#f59e0b",
  "#ef4444",
  "#8b5cf6",
  "#ec4899",
  "#14b8a6",
  "#f97316",
];

const LABEL_MAP = {
  fridge: "Fridge",
  fan: "Table Fan",
  mixer_grinder: "Mixer",
  electric_kettle: "Kettle",
  iron: "Iron",
  washing_machine: "Washing Machine",
  induction_cooker: "Induction Cooker",
};

function ConfidenceBadge({ value }) {
  const pct = Math.round(value * 100);
  const color =
    pct >= 90
      ? "bg-green-100 text-green-800"
      : pct >= 70
      ? "bg-yellow-100 text-yellow-800"
      : "bg-red-100 text-red-800";
  return (
    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${color}`}>
      {pct}% confidence
    </span>
  );
}

export default function AppliancesTab({ recentReadings, readingsLoading = false }) {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!recentReadings || recentReadings.length < 3) {
      setResult(null);
      return;
    }
    setLoading(true);
    setError(null);
    nilmAPI
      .predict(recentReadings)
      .then((data) => setResult(data))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [recentReadings]);

  const predictions = result?.windows || [];
  const chartData = result
    ? Object.entries(
        predictions.reduce((acc, p) => {
          const appliance = p.predicted_appliance;
          const label = LABEL_MAP[appliance] || appliance;
          acc[label] = (acc[label] || 0) + 1;
          return acc;
        }, {})
      ).map(([name, value]) => ({ name, value }))
    : [];

  return (
    <div className="space-y-6">
      {/* Model card */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4 text-sm text-yellow-800">
        <span className="font-semibold">Model note:</span> Smart-plug appliance
        signature classifier — not full aggregate disaggregation. Trained on{" "}
        {result?.classes?.length ?? "—"} classes using feature set{" "}
        {result?.feature_set_version ?? "—"}.
      </div>

      {(readingsLoading || loading) && (
        <div className="text-center text-gray-400 py-12 animate-pulse">
          Running appliance detection…
        </div>
      )}

      {error && (
        <div className="text-center text-red-500 py-8">
          Could not run prediction: {error}
        </div>
      )}

      {!loading && !error && chartData.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Donut chart */}
          <div className="bg-white rounded-2xl shadow-sm p-6">
            <h3 className="text-sm font-semibold text-gray-500 mb-4">
              Detected Appliances
            </h3>
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie
                  data={chartData}
                  cx="50%"
                  cy="50%"
                  innerRadius={65}
                  outerRadius={100}
                  paddingAngle={3}
                  dataKey="value"
                >
                  {chartData.map((_, idx) => (
                    <Cell
                      key={idx}
                      fill={COLORS[idx % COLORS.length]}
                    />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Per-appliance cards */}
          <div className="space-y-3">
            {predictions.slice(0, 8).map((p, idx) => (
              <div
                key={idx}
                className="bg-white rounded-xl shadow-sm p-4 flex items-center justify-between"
              >
                <div>
                  <p className="font-medium text-gray-800">
                    {LABEL_MAP[p.predicted_appliance] || p.predicted_appliance}
                  </p>
                  <p className="text-xs text-gray-400">
                    Window {p.window_index ?? idx + 1}
                  </p>
                </div>
                <ConfidenceBadge value={p.confidence} />
              </div>
            ))}
          </div>
        </div>
      )}

      {!readingsLoading && !loading && !error && chartData.length === 0 && !result && (
        <div className="text-center text-gray-400 py-16">
          <p className="text-4xl mb-3">🔌</p>
          <p>Need at least three recent readings for appliance detection.</p>
        </div>
      )}
    </div>
  );
}
