import { useEffect, useState } from "react";
import { Routes, Route, useNavigate } from "react-router-dom";

import Home from "./pages/Home.jsx"
import Login from "./pages/Login.jsx"
import Register from "./pages/Register.jsx"

function App() {
  const [status, setStatus] = useState({ state: "loading", msg: "" });

  const navigate = useNavigate();

  useEffect(() => {
    let alive = true;

    async function check() {
      try {
        // 1) API alive?
        const h = await fetch("/api/health");
        if (!h.ok) throw new Error("Backend not reachable");

        // 2) DB ok? (we check if /api/books returns JSON)
        const b = await fetch("/api/books");
        if (!b.ok) throw new Error("Database not reachable (books endpoint failed)");

        const data = await b.json();
        if (!Array.isArray(data)) throw new Error("Unexpected API response");

        if (alive) setStatus({ state: "ok", msg: "Database connected" });
      } catch (e) {
        if (alive) setStatus({ state: "err", msg: e?.message || "Connection error" });
      }
    }

    check();
    return () => {
      alive = false;
    };
  }, []);

  const badge =
    status.state === "loading"
      ? { text: "Checking…", cls: "border-white/10 bg-white/5 text-slate-200/80" }
      : status.state === "ok"
        ? { text: "Database connected", cls: "border-emerald-500/20 bg-emerald-500/10 text-emerald-200" }
        : { text: "Not connected", cls: "border-red-500/20 bg-red-500/10 text-red-200" };

return (
  <div className="min-h-screen bg-slate-950 text-slate-100">
    {/* Background glow */}
    <div className="pointer-events-none fixed inset-0 opacity-35">
      <div className="absolute -top-40 left-1/2 h-72 w-[42rem] -translate-x-1/2 rounded-full bg-indigo-500 blur-3xl" />
      <div className="absolute top-20 left-1/2 h-72 w-[42rem] -translate-x-1/2 rounded-full bg-cyan-500 blur-3xl" />
    </div>

    {/* Top Banner (always visible) */}
    <header className="relative z-10 border-b border-white/10 bg-white/5 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        
        {/* Left: Database Status */}
        <div>
          <span className={`rounded-lg border px-2 py-1 text-xs ${badge.cls}`}>
            {badge.text}
          </span>
        </div>

        {/* Center: Title */}
        <h1 className="absolute left-1/2 -translate-x-1/2 text-lg font-semibold tracking-tight">
          NetRank
        </h1>

        {/* Right: Auth Buttons */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate("/login")}
            className="rounded-xl border border-white/20 px-4 py-2 text-sm hover:bg-white/10 transition"
          >
            Login
          </button>

          <button
            onClick={() => navigate("/register")}
            className="rounded-xl bg-indigo-500 px-4 py-2 text-sm font-medium hover:bg-indigo-400 transition"
          >
            Register
          </button>
        </div>
      </div>
    </header>

    {/* Main Content Controlled by Router */}
    <main className="relative z-10 flex min-h-[calc(100vh-80px)] items-center justify-center px-6">
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
      </Routes>
    </main>
  </div>
);
}

export default App
