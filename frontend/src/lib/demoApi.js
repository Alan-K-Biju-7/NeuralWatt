const DEMO_EMAIL = "simulator@neuralwatt.app";
const DEMO_PASSWORD = "Sim@12345";
const now = new Date();
const isoDaysAgo = (days, hour = 12) => {
  const value = new Date(now);
  value.setDate(value.getDate() - days);
  value.setHours(hour, 0, 0, 0);
  return value.toISOString();
};

const dailyUsage = Array.from({ length: 30 }, (_, index) => {
  const daysAgo = 29 - index;
  const weekday = new Date(isoDaysAgo(daysAgo)).getDay();
  const kwh = 6.4 + Math.sin(index / 3) * 1.2 + (weekday === 0 ? 1.1 : 0);
  return { date: isoDaysAgo(daysAgo).slice(0, 10), kwh: Number(kwh.toFixed(3)), avg_watts: Math.round((kwh * 1000) / 24), peak_watts: 1680 + ((index * 137) % 920), reading_count: 288 };
});
const hourlyUsage = Array.from({ length: 24 }, (_, hour) => {
  const morning = Math.exp(-((hour - 8) ** 2) / 7) * 620;
  const evening = Math.exp(-((hour - 20) ** 2) / 9) * 1050;
  const watts = 165 + morning + evening;
  return { hour, avg_watts: Number(watts.toFixed(1)), peak_watts: Math.round(watts * 1.72), reading_count: 84 };
});
const readings = Array.from({ length: 120 }, (_, index) => {
  const timestamp = new Date(now.getTime() - index * 30_000);
  const power = 310 + Math.sin(index / 5) * 85 + (index % 29 < 5 ? 730 : 0);
  return { id: `demo-reading-${index}`, timestamp: timestamp.toISOString(), power_w: Number(power.toFixed(1)), watts: Number(power.toFixed(1)), voltage_v: 231.2, current_a: Number((power / 231.2).toFixed(3)), source: "github_pages_demo" };
});
const totalKwh = dailyUsage.reduce((sum, day) => sum + day.kwh, 0);
const peakHour = hourlyUsage.reduce((peak, item) => item.avg_watts > peak.avg_watts ? item : peak);
const response = (data) => Promise.resolve({ data });
let alertConfig = { id: "demo-alert-config", severity_threshold: "medium", email_enabled: true, email_address: DEMO_EMAIL, webhook_enabled: false, webhook_url: null };
const modelCard = {
  version: "nilm_v1", feature_set: "tapo_signature_v3", n_classes: 6,
  classes: ["electric_kettle", "fan", "fridge", "iron", "mixer_grinder", "washing_machine"],
  test_accuracy: 0.8616, cv_mean_accuracy: 0.7189, cv_std_accuracy: 0.2688,
  cv_strategy: "group_kfold", group_column: "capture_id", group_count: 26,
  limitation: "Smart-plug signature classifier; synchronized aggregate mains data is still required for true NILM.",
  top_feature_importance: [
    { feature: "steady_state_w", importance: 0.222 }, { feature: "p90_power", importance: 0.174 },
    { feature: "active_mean_power", importance: 0.142 }, { feature: "peak_to_mean_ratio", importance: 0.111 },
    { feature: "duty_cycle", importance: 0.094 },
  ],
};

export const demoCredentials = { email: DEMO_EMAIL, password: DEMO_PASSWORD };
export const demoAuthAPI = {
  register: (payload) => response({ id: "demo-user", email: payload.email, full_name: payload.full_name }),
  login: ({ email, password }) => email === DEMO_EMAIL && password === DEMO_PASSWORD
    ? response({ access_token: "neuralwatt-pages-demo", token_type: "bearer" })
    : Promise.reject({ response: { status: 401, data: { detail: "Use the demo credentials shown below." } } }),
  me: () => response({ id: "demo-user", email: DEMO_EMAIL, full_name: "Ancy Biju" }),
};
export const demoHouseholdAPI = {
  create: () => response({}),
  getMine: () => response({ id: "ancy-biju-home", name: "Ancy Biju Home", address: "Kochi, Kerala", num_occupants: 4 }),
  addDevice: () => response({}),
  getDevices: () => response([
    { id: "main-meter", name: "Main Energy Meter", rated_power_watts: 5000, location: "Main panel" },
    { id: "kitchen-meter", name: "Kitchen Circuit", rated_power_watts: 3000, location: "Kitchen" },
  ]),
};
export const demoReadingAPI = { create: () => response(readings[0]), list: () => response({ readings }), stats: () => response({}) };
export const demoAnalyticsAPI = {
  daily: () => response({ from_date: dailyUsage[0].date, to_date: dailyUsage.at(-1).date, total_kwh: Number(totalKwh.toFixed(3)), days: dailyUsage }),
  hourly: () => response({ hours: hourlyUsage, peak_hour: peakHour.hour, peak_hour_avg_watts: peakHour.avg_watts }),
  report: () => response({ anomaly_count: 4, average_daily_kwh: Number((totalKwh / 30).toFixed(2)) }),
  cost: () => response({
    energy_charge: 1047.46, electricity_duty: 104.75, fixed_charge: 130, meter_rent: 15, total_bill: 1297.21,
    slab_breakdown: [
      { slab_label: "0–50", units: 50, rate_per_unit: 3.25, slab_cost: 162.5 },
      { slab_label: "51–100", units: 50, rate_per_unit: 4.05, slab_cost: 202.5 },
      { slab_label: "101–150", units: 50, rate_per_unit: 5.10, slab_cost: 255 },
      { slab_label: "151–200", units: 50, rate_per_unit: 6.95, slab_cost: 347.5 },
      { slab_label: "Above 200", units: 10.46, rate_per_unit: 7.65, slab_cost: 79.96 },
    ],
  }),
};
export const demoAnomalyAPI = {
  list: () => response({ anomalies: [] }), baseline: () => response({ mean_watts: 412.8, std_watts: 121.4, sample_count: 8640 }),
  triggeredAlerts: () => response({ count: 4, triggered_alerts: [
    { id: "alert-1", severity: "high", timestamp: isoDaysAgo(0, 20), reason: "Evening demand exceeded the learned baseline", watts: 2470, expected_watts: 1180, channels: ["email"] },
    { id: "alert-2", severity: "medium", timestamp: isoDaysAgo(2, 8), reason: "Sustained morning load was unusually high", watts: 1680, expected_watts: 930, channels: ["dashboard"] },
    { id: "alert-3", severity: "low", timestamp: isoDaysAgo(6, 1), reason: "Overnight standby usage increased", watts: 390, expected_watts: 180, channels: ["dashboard"] },
    { id: "alert-4", severity: "medium", timestamp: isoDaysAgo(10, 19), reason: "Kitchen circuit peak lasted longer than usual", watts: 2140, expected_watts: 1260, channels: ["email"] },
  ] }),
};
export const demoAlertAPI = {
  create: (_hid, _did, payload) => { alertConfig = { ...payload, id: "demo-alert-config" }; return response(alertConfig); },
  get: () => response(alertConfig), update: (_hid, _did, payload) => { alertConfig = { ...alertConfig, ...payload }; return response(alertConfig); },
  delete: () => response({ deleted: true }),
};
export const demoNilmAPI = {
  predict: () => Promise.resolve({ windows: [{ appliance: "fridge", confidence: 0.89 }] }), modelCard: () => Promise.resolve(modelCard),
  shapImportance: () => Promise.resolve({ source: "model", feature_importance: modelCard.top_feature_importance }),
  dataValidation: () => Promise.resolve({ status: "passed", is_stationary: true, rows: 22723 }),
};
export const demoForecastAPI = { get: () => Promise.resolve({ forecast: Array.from({ length: 24 }, (_, hour) => {
  const timestamp = new Date(now); timestamp.setHours(timestamp.getHours() + hour + 1, 0, 0, 0);
  const predicted = hourlyUsage[timestamp.getHours()].avg_watts / 1000;
  return { hour: timestamp.toISOString(), predicted_kwh: Number(predicted.toFixed(3)), upper_kwh: Number((predicted * 1.16).toFixed(3)) };
}) }) };
export const demoRecommendationAPI = { get: () => Promise.resolve({
  summary: { estimated_daily_cost: 43.24 }, total_estimated_saving_inr: 286,
  recommendations: [
    { id: "shift-washer", title: "Move laundry outside the evening peak", priority: "high", description: "Run the washing machine before 6 PM or after 10 PM to flatten the household peak.", estimated_saving_inr: 148 },
    { id: "standby", title: "Reduce overnight standby load", priority: "medium", description: "The home is drawing about 210 W more than its usual overnight baseline.", estimated_saving_inr: 92 },
    { id: "kitchen", title: "Avoid overlapping high-power kitchen loads", priority: "low", description: "Stagger kettle, iron, and mixer use to reduce short demand spikes.", estimated_saving_inr: 46 },
  ],
}) };
