import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { householdAPI, readingAPI } from "../lib/api";
import useAuthStore from "../store/authStore";
import KPICards from "../components/KPICards";
import DailyChart from "../components/DailyChart";
import HourlyChart from "../components/HourlyChart";
import AnomalyFeed from "../components/AnomalyFeed";
import LiveWattCard from "../components/LiveWattCard";
import AppliancesTab from "../components/dashboard/AppliancesTab";
import ForecastChart from "../components/dashboard/ForecastChart";
import RecommendationsPanel from "../components/dashboard/RecommendationsPanel";
import Settings from "../components/dashboard/Settings";
import {
  Zap, LayoutDashboard, BarChart2,
  Bell, IndianRupee, LogOut, ChevronRight, Menu, X, Home, RefreshCw, Cpu,
  TrendingUp, Lightbulb, Settings as SettingsIcon
} from "lucide-react";

const NAV = [
  { id: "overview",  label: "Overview",  icon: LayoutDashboard },
  { id: "analytics", label: "Analytics", icon: BarChart2 },
  { id: "appliances", label: "Appliances", icon: Cpu },
  { id: "forecast",  label: "Forecast",  icon: TrendingUp },
  { id: "recommendations", label: "Recommendations", icon: Lightbulb },
  { id: "anomalies", label: "Anomalies", icon: Bell },
  { id: "cost",      label: "KSEB Cost", icon: IndianRupee },
  { id: "settings",  label: "Settings",  icon: SettingsIcon },
];

export default function Dashboard() {
  const { user, fetchUser, logout } = useAuthStore();
  const [activeTab, setActiveTab]   = useState("overview");
  const [deviceId,  setDeviceId]    = useState(null);
  const [householdId, setHouseholdId] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => { fetchUser(); }, []);

  const {
    data: household,
    isLoading: householdLoading,
    error: householdError,
    refetch: refetchHousehold,
  } = useQuery({
    queryKey: ["household"],
    queryFn:  async () => {
      const { data } = await householdAPI.getMine();
      return data;
    },
    refetchOnWindowFocus: true,
  });

  useEffect(() => {
    if (household?.id) setHouseholdId(household.id);
  }, [household?.id]);

  const {
    data: devices = [],
    isLoading: devicesLoading,
    error: devicesError,
    refetch: refetchDevices,
  } = useQuery({
    queryKey:  ["devices", householdId],
    enabled:   !!householdId,
    queryFn:   async () => {
      const { data } = await householdAPI.getDevices(householdId);
      return Array.isArray(data) ? data : (data.devices || []);
    },
    initialData: () => household?.devices || [],
    refetchOnWindowFocus: true,
  });

  useEffect(() => {
    if (!devices.length) {
      setDeviceId(null);
      return;
    }
    const selectedDeviceExists = devices.some((device) => device.id === deviceId);
    if (!selectedDeviceExists) setDeviceId(devices[0].id);
  }, [devices, deviceId]);

  const isLoadingDevices = householdLoading || devicesLoading;
  const deviceLoadError = householdError || devicesError;
  const retryDeviceLoad = () => {
    refetchHousehold();
    if (householdId) refetchDevices();
  };
  const selectedDevice = devices.find((device) => device.id === deviceId);
  const {
    data: recentReadings = [],
    isLoading: readingsLoading,
  } = useQuery({
    queryKey: ["appliance-readings", householdId, deviceId],
    enabled: activeTab === "appliances" && !!householdId && !!deviceId,
    queryFn: async () => {
      const { data } = await readingAPI.list(householdId, deviceId, { limit: 120 });
      return data.readings || [];
    },
    refetchInterval: activeTab === "appliances" ? 30000 : false,
  });
  const applianceReadings = useMemo(
    () => recentReadings.slice(0, 60).reverse(),
    [recentReadings]
  );

  return (
    <div className="min-h-screen bg-[#0b1220] text-slate-100 flex">

      {/* Sidebar */}
      <aside className={`
        fixed inset-y-0 left-0 z-50 w-72 bg-[#111827] border-r border-slate-800/90
        flex flex-col transform transition-transform duration-200
        ${sidebarOpen ? "translate-x-0" : "-translate-x-full"}
        lg:relative lg:translate-x-0
      `}>
        {/* Logo */}
        <div className="flex items-center gap-3 px-5 py-5 border-b border-slate-800">
          <div className="w-9 h-9 bg-teal-500 rounded-lg flex items-center justify-center shadow-lg shadow-teal-950/40">
            <Zap className="w-4 h-4 text-white" />
          </div>
          <div>
            <span className="text-white font-semibold text-lg tracking-tight">NeuralWatt</span>
            <p className="text-[11px] text-slate-500">Energy intelligence</p>
          </div>
          <button
            onClick={() => setSidebarOpen(false)}
            className="ml-auto lg:hidden text-slate-400 hover:text-white"
            aria-label="Close sidebar"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Device selector */}
        {devices?.length > 0 && (
          <div className="px-4 py-4 border-b border-slate-800">
            <div className="mb-2 flex items-center justify-between">
              <p className="text-slate-500 text-xs font-semibold uppercase tracking-wider">
                Device
              </p>
              <span className="rounded-full bg-slate-800 px-2 py-0.5 text-[11px] text-slate-400">
                {devices.length} active
              </span>
            </div>
            <select
              value={deviceId || ""}
              onChange={(e) => setDeviceId(e.target.value)}
              className="w-full bg-slate-900/80 border border-slate-700 text-white text-sm
                         rounded-lg px-3 py-3 focus:outline-none focus:ring-2 focus:ring-teal-500/50"
            >
              {devices.map((d) => (
                <option key={d.id} value={d.id}>{d.name}</option>
              ))}
            </select>
          </div>
        )}

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 space-y-1.5">
          {NAV.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => { setActiveTab(id); setSidebarOpen(false); }}
              className={`
                w-full flex items-center gap-3 px-3 py-3 rounded-lg text-sm font-medium
                transition-colors duration-150 border
                ${activeTab === id
                  ? "bg-teal-500/10 text-teal-300 border-teal-500/20"
                  : "text-slate-400 hover:text-white hover:bg-slate-800/80 border-transparent"}
              `}
            >
              <Icon className="w-4 h-4" />
              {label}
              {activeTab === id && <ChevronRight className="w-3 h-3 ml-auto" />}
            </button>
          ))}
        </nav>

        {/* User + Logout */}
        <div className="px-4 py-4 border-t border-slate-800">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-9 h-9 bg-slate-800 rounded-lg flex items-center
                            justify-center text-teal-300 font-semibold text-sm">
              {(user?.full_name || user?.name || user?.email || "U")?.[0]?.toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-white text-sm font-medium truncate">{user?.full_name || user?.name}</p>
              <p className="text-slate-500 text-xs truncate">{user?.email}</p>
            </div>
          </div>
          <button
            onClick={logout}
            className="w-full flex items-center gap-2 text-slate-400 hover:text-red-400
                       text-sm px-3 py-2.5 rounded-lg hover:bg-slate-800 transition-colors"
          >
            <LogOut className="w-4 h-4" />
            Sign out
          </button>
        </div>
      </aside>

      {/* Overlay for mobile */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0">

        {/* Top bar */}
        <header className="bg-[#111827]/95 border-b border-slate-800 px-5 sm:px-8 py-4
                           flex items-center justify-between gap-4">
          <button
            onClick={() => setSidebarOpen(true)}
            className="lg:hidden text-slate-400 hover:text-white"
            aria-label="Open sidebar"
          >
            <Menu className="w-5 h-5" />
          </button>
          <div className="min-w-0">
            <h1 className="text-white font-semibold text-xl capitalize tracking-tight">{activeTab}</h1>
            <p className="text-slate-400 text-sm truncate">
              {household?.address || "Kerala, India"} · KSEB tariff
            </p>
          </div>
          <div className="ml-auto hidden md:flex items-center gap-3">
            <div className="flex items-center gap-2 rounded-lg border border-slate-800 bg-slate-900/70 px-3 py-2 text-sm text-slate-300">
              <Home className="h-4 w-4 text-teal-300" />
              <span className="max-w-48 truncate">{household?.name || "Home"}</span>
            </div>
            {selectedDevice && (
              <div className="rounded-lg border border-slate-800 bg-slate-900/70 px-3 py-2 text-sm text-slate-300">
                {selectedDevice.rated_power_watts?.toLocaleString()} W rated
              </div>
            )}
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-auto">
          <div className="mx-auto w-full max-w-[1680px] p-4 sm:p-6 lg:p-8">
          {isLoadingDevices ? (
            <div className="flex items-center justify-center h-72 text-slate-500">
              <div className="flex items-center gap-3 rounded-lg border border-slate-800 bg-slate-900/70 px-4 py-3">
                <RefreshCw className="h-4 w-4 animate-spin text-teal-300" />
                <span className="text-sm">Loading devices</span>
              </div>
            </div>
          ) : deviceLoadError ? (
            <div className="flex flex-col items-center justify-center h-72 gap-3 text-center">
              <p className="max-w-xl text-slate-400">
                Could not load devices. Check that the backend is running and you are signed in with the same account used in Swagger.
              </p>
              <button
                onClick={retryDeviceLoad}
                className="rounded-lg bg-teal-500 px-4 py-2 text-sm font-medium text-white hover:bg-teal-400"
              >
                Retry
              </button>
            </div>
          ) : !deviceId ? (
            <div className="flex flex-col items-center justify-center h-72 gap-3 text-center">
              <p className="text-slate-500">No devices found for this household.</p>
              <button
                onClick={() => refetchDevices()}
                className="rounded-lg bg-slate-800 px-4 py-2 text-sm font-medium text-slate-200 hover:bg-slate-700"
              >
                Refresh devices
              </button>
            </div>
          ) : (
            <>
              {activeTab === "overview" && (
                <div className="space-y-6">
                  <LiveWattCard
                    householdId={householdId}
                    deviceId={deviceId}
                    deviceName={selectedDevice?.name}
                  />
                  <KPICards householdId={householdId} deviceId={deviceId} />
                  <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                    <DailyChart householdId={householdId} deviceId={deviceId} />
                    <HourlyChart householdId={householdId} deviceId={deviceId} />
                  </div>
                  <AnomalyFeed householdId={householdId} deviceId={deviceId} />
                </div>
              )}
              {activeTab === "analytics" && (
                <div className="space-y-6">
                  <DailyChart householdId={householdId} deviceId={deviceId} days={30} />
                  <HourlyChart householdId={householdId} deviceId={deviceId} days={30} />
                </div>
              )}
              {activeTab === "appliances" && (
                <AppliancesTab
                  recentReadings={applianceReadings}
                  readingsLoading={readingsLoading}
                />
              )}
              {activeTab === "forecast" && (
                <ForecastChart householdId={householdId} />
              )}
              {activeTab === "recommendations" && (
                <RecommendationsPanel householdId={householdId} />
              )}
              {activeTab === "anomalies" && (
                <AnomalyFeed householdId={householdId} deviceId={deviceId} limit={50} />
              )}
              {activeTab === "cost" && (
                <KPICards householdId={householdId} deviceId={deviceId} costOnly />
              )}
              {activeTab === "settings" && (
                <Settings householdId={householdId} deviceId={deviceId} />
              )}
            </>
          )}
          </div>
        </main>
      </div>
    </div>
  );
}
