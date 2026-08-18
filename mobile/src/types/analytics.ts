export type DailyUsagePoint = { date: string; kwh: number; avg_watts: number; peak_watts: number; reading_count: number };
export type HourlyUsagePoint = { hour: number; avg_watts: number; peak_watts: number; reading_count: number };

export type DailyUsage = { device_id: string; unit: string; days: DailyUsagePoint[]; total_kwh: number; from_date: string; to_date: string };
export type HourlyUsage = { device_id: string; hours: HourlyUsagePoint[]; peak_hour: number; peak_hour_avg_watts: number };

export type CostEstimate = {
  total_kwh: number;
  energy_charge: number;
  fixed_charge: number;
  electricity_duty: number;
  meter_rent: number;
  total_bill: number;
  currency: string;
};
