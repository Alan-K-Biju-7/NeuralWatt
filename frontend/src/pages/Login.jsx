import { useState } from "react";
import { useNavigate } from "react-router-dom";
import useAuthStore from "../store/authStore";
import { Zap, Mail, Lock, User, AlertCircle } from "lucide-react";
import { demoCredentials } from "../lib/demoApi";
import { IS_DEMO } from "../lib/api";

export default function Login() {
  const [mode, setMode]       = useState("login");   // "login" | "register"
  const [name, setName]       = useState("");
  const [email, setEmail]     = useState(IS_DEMO ? demoCredentials.email : "");
  const [password, setPass]   = useState(IS_DEMO ? demoCredentials.password : "");
  const navigate              = useNavigate();
  const { login, register, isLoading, error, clearError } = useAuthStore();

  const handleSubmit = async (e) => {
    e.preventDefault();
    clearError();
    let ok = false;
    if (mode === "login") {
      ok = await login(email, password);
    } else {
      ok = await register(name, email, password);
      if (ok) {
        ok = await login(email, password);
      }
    }
    if (ok) navigate("/");
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900
                    flex items-center justify-center p-4">
      <div className="w-full max-w-md">

        {/* Logo */}
        <div className="flex items-center justify-center gap-3 mb-8">
          <div className="w-10 h-10 bg-teal-500 rounded-xl flex items-center justify-center">
            <Zap className="w-6 h-6 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">NeuralWatt</h1>
        </div>

        {/* Card */}
        <div className="bg-slate-800 border border-slate-700 rounded-2xl p-8 shadow-2xl">
          <h2 className="text-xl font-semibold text-white mb-1">
            {mode === "login" ? "Welcome back" : "Create account"}
          </h2>
          <p className="text-slate-400 text-sm mb-6">
            {mode === "login"
              ? "Sign in to your energy dashboard"
              : "Start monitoring your energy usage"}
          </p>

          {IS_DEMO && mode === "login" && (
            <div className="mb-5 rounded-lg border border-teal-500/25 bg-teal-500/10 px-4 py-3 text-xs text-teal-100">
              <p className="font-semibold">Public demo account</p>
              <p className="mt-1 font-mono">{demoCredentials.email}</p>
              <p className="font-mono">{demoCredentials.password}</p>
            </div>
          )}

          {error && (
            <div className="flex items-center gap-2 bg-red-500/10 border border-red-500/30
                            text-red-400 rounded-lg px-4 py-3 mb-4 text-sm">
              <AlertCircle className="w-4 h-4 shrink-0" />
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {mode === "register" && (
              <div>
                <label className="text-slate-300 text-sm font-medium block mb-1.5">
                  Full name
                </label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    required
                    placeholder="Ancy Biju"
                    className="w-full bg-slate-700 border border-slate-600 rounded-lg
                               pl-10 pr-4 py-2.5 text-white placeholder-slate-400 text-sm
                               focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                  />
                </div>
              </div>
            )}

            <div>
              <label className="text-slate-300 text-sm font-medium block mb-1.5">
                Email address
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  placeholder="you@example.com"
                  className="w-full bg-slate-700 border border-slate-600 rounded-lg
                             pl-10 pr-4 py-2.5 text-white placeholder-slate-400 text-sm
                             focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                />
              </div>
            </div>

            <div>
              <label className="text-slate-300 text-sm font-medium block mb-1.5">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPass(e.target.value)}
                  required
                  placeholder="••••••••"
                  className="w-full bg-slate-700 border border-slate-600 rounded-lg
                             pl-10 pr-4 py-2.5 text-white placeholder-slate-400 text-sm
                             focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-teal-500 hover:bg-teal-400 disabled:bg-teal-500/50
                         text-white font-semibold rounded-lg py-2.5 text-sm
                         transition-colors duration-200 mt-2"
            >
              {isLoading
                ? "Please wait..."
                : mode === "login" ? "Sign in" : "Create account"}
            </button>
          </form>

          <div className="mt-6 text-center text-sm text-slate-400">
            {mode === "login" ? "Don't have an account? " : "Already have an account? "}
            <button
              onClick={() => { setMode(mode === "login" ? "register" : "login"); clearError(); }}
              className="text-teal-400 hover:text-teal-300 font-medium transition-colors"
            >
              {mode === "login" ? "Sign up" : "Sign in"}
            </button>
          </div>
        </div>

        <p className="text-center text-slate-500 text-xs mt-6">
          NeuralWatt · Kerala KSEB Energy Monitor
        </p>
      </div>
    </div>
  );
}
