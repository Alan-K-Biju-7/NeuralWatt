export type Anomaly = {
  id: string;
  watts: number;
  expected_watts: number;
  deviation_pct: number;
  severity: "low" | "medium" | "high" | string;
  message?: string;
  detected_at: string;
};

export type AnomalyResponse = { device_id: string; anomalies: Anomaly[]; total: number };

export type Recommendation = {
  id?: string;
  title: string;
  message: string;
  severity: string;
  savings_hint: string;
};

export type ForecastPoint = {
  hour: string;
  predicted_kwh: number;
  lower_kwh: number;
  upper_kwh: number;
};

export type RecommendationResponse = { household_id: string; window_hours: number; recommendations: Recommendation[] };
export type ForecastResponse = { household_id: string; history_days: number; horizon_hours: number; forecast: ForecastPoint[] };
