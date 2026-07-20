import axios from "axios";
import {
  demoAlertAPI, demoAnalyticsAPI, demoAnomalyAPI, demoAuthAPI,
  demoForecastAPI, demoHouseholdAPI, demoNilmAPI, demoReadingAPI,
  demoRecommendationAPI,
} from "./demoApi";

export const IS_DEMO = import.meta.env.VITE_DEMO_MODE === "true";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

const api = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("nw_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("nw_token");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

const liveAuthAPI = {
  register: (data) => api.post("/auth/register", data),
  login:    (data) => api.post("/auth/login",    data),
  me:       ()     => api.get("/auth/me"),
};

const liveHouseholdAPI = {
  create:     (data)        => api.post("/households", data),
  getMine:    ()            => api.get("/households/me"),
  addDevice:  (hid, data)   => api.post(`/households/${hid}/devices`, data),
  getDevices: (hid)         => api.get(`/households/${hid}/devices`),
};

const liveReadingAPI = {
  create: (hid, did, data) =>
    api.post(`/households/${hid}/devices/${did}/readings`, data),
  list: (hid, did, params) =>
    api.get(`/households/${hid}/devices/${did}/readings`, { params }),
  stats: (hid, did, params) =>
    api.get(`/households/${hid}/devices/${did}/stats`, { params }),
};

const liveAnomalyAPI = {
  list: (hid, did, params) =>
    api.get(`/households/${hid}/devices/${did}/anomalies`, { params }),
  baseline: (hid, did) =>
    api.get(`/households/${hid}/devices/${did}/baseline`),
  triggeredAlerts: (hid, limit = 20) =>
    api.get("/anomalies/triggered-alerts", {
      params: { household_id: hid, limit },
    }),
};

const liveAlertAPI = {
  create: (hid, did, data) =>
    api.post(`/households/${hid}/devices/${did}/alert-config`, data),
  get:    (hid, did)       =>
    api.get(`/households/${hid}/devices/${did}/alert-config`),
  update: (hid, did, data) =>
    api.patch(`/households/${hid}/devices/${did}/alert-config`, data),
  delete: (hid, did)       =>
    api.delete(`/households/${hid}/devices/${did}/alert-config`),
};

const liveAnalyticsAPI = {
  daily:   (hid, did, days = 30) =>
    api.get(`/households/${hid}/devices/${did}/analytics/daily`,   { params: { days } }),
  hourly:  (hid, did, days = 7)  =>
    api.get(`/households/${hid}/devices/${did}/analytics/hourly`,  { params: { days } }),
  report:  (hid, did, period = "monthly") =>
    api.get(`/households/${hid}/devices/${did}/analytics/report`,  { params: { period } }),
  cost:    (hid, did, days = 30) =>
    api.get(`/households/${hid}/devices/${did}/analytics/cost`,    { params: { days } }),
};

const liveNilmAPI = {
  predict: (readings, windowSizeS = 30) =>
    api.post("/nilm/predict", {
      readings,
      window_size_s: windowSizeS,
    }).then((res) => res.data),
  modelCard: () => api.get("/nilm/model-card").then((res) => res.data),
  shapImportance: () => api.get("/nilm/shap").then((res) => res.data),
  dataValidation: () => api.get("/nilm/data-validation").then((res) => res.data),
};

const liveForecastAPI = {
  get: (hid, days = 30) =>
    api.get(`/forecast/${hid}`, { params: { days } }).then((res) => res.data),
};

const liveRecommendationAPI = {
  get: (hid) => api.get(`/recommendations/${hid}`).then((res) => res.data),
};

export const authAPI = IS_DEMO ? demoAuthAPI : liveAuthAPI;
export const householdAPI = IS_DEMO ? demoHouseholdAPI : liveHouseholdAPI;
export const readingAPI = IS_DEMO ? demoReadingAPI : liveReadingAPI;
export const anomalyAPI = IS_DEMO ? demoAnomalyAPI : liveAnomalyAPI;
export const alertAPI = IS_DEMO ? demoAlertAPI : liveAlertAPI;
export const analyticsAPI = IS_DEMO ? demoAnalyticsAPI : liveAnalyticsAPI;
export const nilmAPI = IS_DEMO ? demoNilmAPI : liveNilmAPI;
export const forecastAPI = IS_DEMO ? demoForecastAPI : liveForecastAPI;
export const recommendationAPI = IS_DEMO ? demoRecommendationAPI : liveRecommendationAPI;

export default api;
