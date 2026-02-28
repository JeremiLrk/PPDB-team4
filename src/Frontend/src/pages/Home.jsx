import { useNavigate } from "react-router-dom"

function Home() {
    const navigate = useNavigate()

    return (
        <div className="min-h-screen bg-slate-950 text-slate-100">

            <div className="relative mx-auto w-full max-w-6xl px-6 py-20">
                
                <section className="text-center">
                    <h1 className="text-5xl font-semibold tracking-tight">
                        NetRank
                    </h1>

                    <p className="mt-6 text-lg text-slate-300/70">
                        Compete. Challenge. Climb the ladder.
                    </p>

                    <p className="mt-2 text-sm text-slate-400">
                        The competitive ranking system for tennis and padel clubs.
                    </p>

                    <div className="mt-10 flex justify-center gap-4">
                        <button
                            onClick={() => navigate("/register")}
                            className="rounded-xl bg-indigo-500 px-6 py-3 font-medium hover:bg-indigo-400 transition"
                        >
                            Join the Ladder
                        </button>

                        <button
                            onClick={() => navigate("/login")}
                            className="rounded-xl border border-white/20 px-6 py-3 hover:bg-white/10 transition"
                        >
                            Login
                        </button>
                    </div>
                </section>

                <section className="mt-20 rounded-3xl border border-white/10 bg-white/5 p-10 backdrop-blur">
                    <h2 className="text-xl font-semibold mb-6">
                        Top Players
                    </h2>

                    <div className="space-y-4 text-sm">
                        <div className="flex justify-between">
                            <span>#1 Alex</span>
                            <span>1450 pts</span>
                        </div>
                        <div className="flex justify-between">
                            <span>#2 Emma</span>
                            <span>1390 pts</span>
                        </div>
                        <div className="flex justify-between">
                            <span>#3 Liam</span>
                            <span>1320 pts</span>
                        </div>
                    </div>
                </section>

                <section className="mt-20 grid gap-6 md:grid-cols-3">
                    <div className="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
                        <h3 className="font-semibold">Real-Time Rankings</h3>
                        <p className="mt-2 text-sm text-slate-300/70">
                            Rankings update automatically after each match result.
                        </p>
                    </div>

                    <div className="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
                        <h3 className="font-semibold">Challenge System</h3>
                        <p className="mt-2 text-sm text-slate-300/70">
                            Challenge players above you to move up the ladder.
                        </p>
                    </div>

                    <div className="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
                        <h3 className="font-semibold">Match History</h3>
                        <p className="mt-2 text-sm text-slate-300/70">
                            Track all played matches and performance statistics.
                        </p>
                    </div>
                </section>

            </div>
        </div>
    )
}

export default Home
