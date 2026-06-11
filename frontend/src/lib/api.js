import axios from "axios";

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

export const authAPI = {
  register: (data) => api.post("/auth/register", data),
  login:    (data) => api.post("/auth/login",    data),
  me:       ()     => api.get("/auth/me"),
};

export const householdAPI = {
  create:     (data)        => api.post("/households", data),
  getMine:    ()            => api.get("/households/me"),
  addDevice:  (hid, data)   => api.post(`/households/${hid}/devices`, data),
  getDevices: (hid)         => api.get(`/households/${hid}/devices`),
};

export const readingAPI = {
  create: (hid, did, data) =>
    api.post(`/households/${hid}/devices/${did}/readings`, data),
  list: (hid, did, params) =>
    api.get(`/households/${hid}/devices/${did}/readings`, { params }),
  stats: (hid, did, params) =>
    api.get(`/households/${hid}/devices/${did}/stats`, { params }),
};

export const anomalyAPI = {
  list: (hid, did, params) =>
    api.get(`/households/${hid}/devices/${did}/anomalies`, { params }),
  baseline: (hid, did) =>
    api.get(`/households/${hid}/devices/${did}/baseline`),
};

export const alertAPI = {
  create: (hid, did, data) =>
    api.post(`/households/${hid}/devices/${did}/alert-config`, data),
  get:    (hid, did)       =>
    api.get(`/households/${hid}/devices/${did}/alert-config`),
  update: (hid, did, data) =>
    api.patch(`/households/${hid}/devices/${did}/alert-config`, data),
  delete: (hid, did)       =>
    api.delete(`/households/${hid}/devices/${did}/alert-config`),
};

export const analyticsAPI = {
  daily:   (hid, did, days = 30) =>
    api.get(`/households/${hid}/devices/${did}/analytics/daily`,   { params: { days } }),
  hourly:  (hid, did, days = 7)  =>
    api.get(`/households/${hid}/devices/${did}/analytics/hourly`,  { params: { days } }),
  report:  (hid, did, period = "monthly") =>
    api.get(`/households/${hid}/devices/${did}/analytics/report`,  { params: { period } }),
  cost:    (hid, did, days = 30) =>
    api.get(`/households/${hid}/devices/${did}/analytics/cost`,    { params: { days } }),
};

export const nilmAPI = {
  predict: (readings, windowSizeS = 30) =>
    api.post("/nilm/predict", {
      readings,
      window_size_s: windowSizeS,
    }).then((res) => res.data),
};

export default api;
