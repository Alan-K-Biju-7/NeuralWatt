export type EnergyReading = {
  id?: string;
  power_w: number;
  voltage_v: number;
  current_a: number;
  energy_kwh: number;
  frequency_hz?: number | null;
  power_factor?: number | null;
  source: string;
  timestamp: string;
};

export type ReadingPage = {
  readings: EnergyReading[];
  total: number;
};
