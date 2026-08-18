export type DailyUsagePoint = { date: string; energy_kwh: number; cost?: number };
export type HourlyUsagePoint = { hour: number; energy_kwh: number; average_power_w?: number };

export type DailyUsage = { household_id: string; device_id: string; days: number; data: DailyUsagePoint[] };
export type HourlyUsage = { household_id: string; device_id: string; days: number; data: HourlyUsagePoint[] };

export type CostEstimate = {
  energy_kwh: number;
  energy_charge: number;
  fixed_charge: number;
  duty: number;
  meter_rent: number;
  total_cost: number;
  currency: string;
};
