import { useEffect, useState } from "react"

function Home() {
    const [status, setStatus] = useState({ state: "loading", msg: "" })

    useEffect(() => {
        let alive = true

        async function check() {
            try {
                // API + DB status from health endpoint
                const h = await fetch("/api/health")
                const data = await h.json()
                if (!h.ok || !data?.db_connected)
                    throw new Error(data?.msg || "Database not reachable")

                if (alive) setStatus({ state: "ok", msg: "Database connected" })
            } catch (e) {
                if (alive)
                    setStatus({
                        state: "err",
                        msg: e?.message || "Connection error",
                    })
            }
        }

        check()
        return () => {
            alive = false
        }
    }, [])

    const badge =
        status.state === "loading"
            ? {
                  text: "Checking…",
                  cls: "border-white/10 bg-white/5 text-slate-200/80",
              }
            : status.state === "ok"
              ? {
                    text: "Database connected",
                    cls: "border-emerald-500/20 bg-emerald-500/10 text-emerald-200",
                }
              : {
                    text: "Not connected",
                    cls: "border-red-500/20 bg-red-500/10 text-red-200",
                }

    return (
        <div className="min-h-screen bg-slate-950 text-slate-100">
            <div className="pointer-events-none fixed inset-0 opacity-35">
                <div className="absolute -top-40 left-1/2 h-72 w-[42rem] -translate-x-1/2 rounded-full bg-indigo-500 blur-3xl" />
                <div className="absolute top-20 left-1/2 h-72 w-[42rem] -translate-x-1/2 rounded-full bg-cyan-500 blur-3xl" />
            </div>

            <div className="relative mx-auto w-full max-w-6xl px-6 py-16">
                <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
                    {/* Left: hero */}
                    <section className="rounded-3xl border border-white/10 bg-white/5 p-10 backdrop-blur">
                        <p className="text-sm text-slate-300/70">PPDB Team 4</p>

                        <h1 className="mt-3 text-4xl font-semibold tracking-tight">
                            Web-based Club Ladder
                        </h1>

                        <p className="mt-6 text-sm text-slate-300/70">
                            React frontend + Flask REST API + PostgreSQL +
                            Tailwind CSS.
                        </p>
                    </section>

                    {/* Right: status */}
                    <aside className="rounded-3xl border border-white/10 bg-white/5 p-8 backdrop-blur">
                        <p className="text-sm font-semibold text-slate-200/90">
                            Status
                        </p>

                        <div className="mt-4 space-y-3">
                            <div className="flex items-center justify-between gap-3">
                                <span className="text-sm text-slate-300/70">
                                    Database
                                </span>
                                <span
                                    className={`rounded-lg border px-2 py-1 text-xs ${badge.cls}`}
                                >
                                    {badge.text}
                                </span>
                            </div>
                        </div>

                        {status.state === "err" && (
                            <p className="mt-4 text-xs text-red-200/80">
                                {status.msg}
                            </p>
                        )}
                    </aside>
                </div>
            </div>
        </div>
    )
}

export default Home
