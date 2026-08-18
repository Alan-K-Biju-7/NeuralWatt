export type Anomaly = {
  id: string;
  power_w: number;
  z_score: number;
  severity: "low" | "medium" | "high" | string;
  message?: string;
  timestamp: string;
};

export type Recommendation = {
  id?: string;
  title: string;
  description: string;
  category?: string;
  estimated_savings?: number;
};

export type ForecastPoint = {
  timestamp: string;
  predicted_power_w?: number;
  predicted_kwh?: number;
};
