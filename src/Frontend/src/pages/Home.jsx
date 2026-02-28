import { useNavigate } from "react-router-dom"
import background from "../assets/background.webp"

function Home() {
    const navigate = useNavigate()

    return (
        <div className="grid gap-10 lg:grid-cols-[1fr_2fr_1fr] items-start">

        {/* LEFT — LADDER */}
        <aside className="flex flex-col gap-6">

        <section className="rounded-3xl border border-white/10 bg-white/5 p-8 backdrop-blur h-fit">
            <h2 className="text-xl font-semibold mb-6">Ladders</h2>

            <div className="flex flex-col gap-4 text-sm">

            <button
                onClick={() => navigate("/ladder")}
                className="text-left rounded-xl border border-white/10 px-4 py-3 hover:bg-white/10 transition"
            >
                Men’s Tennis
            </button>

            <button
                onClick={() => navigate("/ladder")}
                className="text-left rounded-xl border border-white/10 px-4 py-3 hover:bg-white/10 transition"
            >
                Women’s Tennis
            </button>

            <button
                onClick={() => navigate("/ladder")}
                className="text-left rounded-xl border border-white/10 px-4 py-3 hover:bg-white/10 transition"
            >
                Padel
            </button>

            <button
                onClick={() => navigate("/ladder")}
                className="text-left rounded-xl border border-white/10 px-4 py-3 hover:bg-white/10 transition"
            >
                Juniors
            </button>

            </div>
        </section>

        </aside>

        {/* CENTER — PICTURE */}
        <section className="text-center">
            <h1 className="text-5xl font-semibold tracking-tight">
            NetRank
            </h1>

            <img src={background} alt="Tennis match" className="mt-6 rounded-2xl w-full"/>

            <p className="mt-6 text-lg text-slate-300/70">
            Compete. Challenge. Climb the ladder.
            </p>

            <p className="mt-2 text-sm text-slate-400">
            The competitive ranking system for tennis and padel clubs.
            </p>

            <div className="mt-10 flex justify-center gap-4">
            <button
                onClick={() => navigate("/register")}
                className="rounded-xl bg-indigo-500 px-6 py-3 font-medium hover:bg-indigo-400 transition">
                Join the Ladder
            </button>

            <button
                onClick={() => navigate("/login")}
                className="rounded-xl border border-white/20 px-6 py-3 hover:bg-white/10 transition">
                Login
            </button>
            </div>
        </section>


        {/* RIGHT — SCOREBOARDS */}
        <aside className= "flex flex-col gap-8">
            <section className="rounded-3xl border border-white/10 bg-white/5 p-8 backdrop-blur h-fit">
                <h2 className="text-xl font-semibold mb-6">Top Players</h2>

                <div className="space-y-4 text-sm">
                <div className="flex justify-between">
                    <span>#1 Lorem</span>
                    <span>Ipsum</span>
                </div>
                <div className="flex justify-between">
                    <span>#2 Lorem</span>
                    <span>Ipsum</span>
                </div>
                <div className="flex justify-between">
                    <span>#3 Lorem</span>
                    <span>Ipsum</span>
                </div>
                </div>
            </section>
            <section className="rounded-3xl border border-white/10 bg-white/5 p-8 backdrop-blur h-fit">
                <h2 className="text-xl font-semibold mb-6">Top Matches</h2>

                <div className="space-y-4 text-sm">
                <div className="flex justify-between">
                    <span>Lorem vs Ipsum</span>
                    <span>Pending</span>
                </div>
                <div className="flex justify-between">
                    <span>Dolor vs Sit</span>
                    <span>Pending</span>
                </div>
                <div className="flex justify-between">
                    <span>Amet vs Consectetur</span>
                    <span>Pending</span>
                </div>
                </div>
            </section>
        </aside>

        </div>
    )
}

export default Home
