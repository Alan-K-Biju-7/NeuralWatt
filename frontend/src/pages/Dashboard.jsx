import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { householdAPI } from "../lib/api";
import useAuthStore from "../store/authStore";
import KPICards from "../components/KPICards";
import DailyChart from "../components/DailyChart";
import HourlyChart from "../components/HourlyChart";
import AnomalyFeed from "../components/AnomalyFeed";
import LiveWattCard from "../components/LiveWattCard";
import {
  Zap, LayoutDashboard, BarChart2,
  Bell, IndianRupee, LogOut, ChevronRight, Menu, X
} from "lucide-react";

const NAV = [
  { id: "overview",  label: "Overview",  icon: LayoutDashboard },
  { id: "analytics", label: "Analytics", icon: BarChart2 },
  { id: "anomalies", label: "Anomalies", icon: Bell },
  { id: "cost",      label: "KSEB Cost", icon: IndianRupee },
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

  return (
    <div className="min-h-screen bg-slate-900 flex">

      {/* Sidebar */}
      <aside className={`
        fixed inset-y-0 left-0 z-50 w-64 bg-slate-800 border-r border-slate-700
        flex flex-col transform transition-transform duration-200
        ${sidebarOpen ? "translate-x-0" : "-translate-x-full"}
        lg:relative lg:translate-x-0
      `}>
        {/* Logo */}
        <div className="flex items-center gap-3 px-6 py-5 border-b border-slate-700">
          <div className="w-8 h-8 bg-teal-500 rounded-lg flex items-center justify-center">
            <Zap className="w-4 h-4 text-white" />
          </div>
          <span className="text-white font-bold text-lg tracking-tight">NeuralWatt</span>
          <button
            onClick={() => setSidebarOpen(false)}
            className="ml-auto lg:hidden text-slate-400 hover:text-white"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Device selector */}
        {devices?.length > 0 && (
          <div className="px-4 py-3 border-b border-slate-700">
            <p className="text-slate-500 text-xs font-medium uppercase tracking-wider mb-2">
              Device
            </p>
            <select
              value={deviceId || ""}
              onChange={(e) => setDeviceId(e.target.value)}
              className="w-full bg-slate-700 border border-slate-600 text-white text-sm
                         rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-teal-500"
            >
              {devices.map((d) => (
                <option key={d.id} value={d.id}>{d.name}</option>
              ))}
            </select>
          </div>
        )}

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 space-y-1">
          {NAV.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => { setActiveTab(id); setSidebarOpen(false); }}
              className={`
                w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium
                transition-colors duration-150
                ${activeTab === id
                  ? "bg-teal-500/15 text-teal-400"
                  : "text-slate-400 hover:text-white hover:bg-slate-700"}
              `}
            >
              <Icon className="w-4 h-4" />
              {label}
              {activeTab === id && <ChevronRight className="w-3 h-3 ml-auto" />}
            </button>
          ))}
        </nav>

        {/* User + Logout */}
        <div className="px-4 py-4 border-t border-slate-700">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-8 h-8 bg-teal-500/20 rounded-full flex items-center
                            justify-center text-teal-400 font-semibold text-sm">
              {user?.name?.[0]?.toUpperCase() || "U"}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-white text-sm font-medium truncate">{user?.full_name || user?.name}</p>
              <p className="text-slate-500 text-xs truncate">{user?.email}</p>
            </div>
          </div>
          <button
            onClick={logout}
            className="w-full flex items-center gap-2 text-slate-400 hover:text-red-400
                       text-sm px-3 py-2 rounded-lg hover:bg-slate-700 transition-colors"
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
        <header className="bg-slate-800 border-b border-slate-700 px-6 py-4
                           flex items-center gap-4">
          <button
            onClick={() => setSidebarOpen(true)}
            className="lg:hidden text-slate-400 hover:text-white"
          >
            <Menu className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-white font-semibold text-lg capitalize">{activeTab}</h1>
            <p className="text-slate-400 text-xs">
              {household?.address || "Kerala, India"} · KSEB Tariff
            </p>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 p-6 overflow-auto">
          {isLoadingDevices ? (
            <div className="flex items-center justify-center h-64 text-slate-500">
              Loading devices...
            </div>
          ) : deviceLoadError ? (
            <div className="flex flex-col items-center justify-center h-64 gap-3 text-center">
              <p className="text-slate-400">
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
            <div className="flex flex-col items-center justify-center h-64 gap-3 text-center">
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
                <LiveWattCard householdId={householdId} />
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
              {activeTab === "anomalies" && (
                <AnomalyFeed householdId={householdId} deviceId={deviceId} limit={50} />
              )}
              {activeTab === "cost" && (
                <KPICards householdId={householdId} deviceId={deviceId} costOnly />
              )}
            </>
          )}
        </main>
      </div>
    </div>
  );
}
