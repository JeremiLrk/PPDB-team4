// Page container for Home.

import { useNavigate } from "react-router-dom"
import tennisBackground from "@/assets/tennis.jpg"
import styles from "@/style/Home.module.css"


function Home() {
    const navigate = useNavigate()
    /*
     Renders the public landing page and its navigation shortcuts.
    */

    return (
        <div className={styles.container}>

        {/* LEFT — LADDER */}
            <aside className={styles.ladderAside}>
                {/* Admin Button placed at the top of the sidebar */}
    <button 
        onClick={() => navigate("/admin")}
        className="w-full rounded-xl bg-white/5 border border-white/10 px-3 py-2 text-xs font-medium hover:bg-white/10 transition mb-2"
    >
        ⚙️ Beheerdersdashboard
    </button>

                <section className={styles.ladderContainer}>
                    <h2 className={styles.ladderContainerText}>Ladders</h2>

                    <div className={styles.ladderCard}>

                        <button
                            onClick={() => navigate("/ladder")}
                            className={styles.ladderButton}
                        >
                            Heren tennis
                        </button>

                        <button
                            onClick={() => navigate("/ladder")}
                            className={styles.ladderButton}
                        >
                            Dames tennis
                        </button>

                        <button
                            onClick={() => navigate("/ladder")}
                            className={styles.ladderButton}
                        >
                            Padel
                        </button>

                        <button
                            onClick={() => navigate("/ladder")}
                            className={styles.ladderButton}
                        >
                            Junioren
                        </button>

                        <div className={styles.ladderCard}>

                            <section className="text-center">
                                <h1 className="text-3xl font-semibold tracking-tight">
                                    NetRank
                                </h1>
                            </section>
                        </div>
                    </div>
                </section>
            </aside>

        {/* CENTER — PICTURE */}
        <section className="text-center">
            <h1 className="text-5xl font-semibold tracking-tight">
            NetRank
            </h1>

            <img src={tennisBackground} alt="Tennis match" className="mt-6 rounded-2xl w-full"/>

            <p className="mt-6 text-lg text-slate-300/70">
            Speel. Daag uit. Klim op de ladder.
            </p>

            <p className="mt-2 text-sm text-slate-400">
            Het competitieve rankingsysteem voor tennis- en padelclubs.
            </p>

            <div className="mt-10 flex justify-center gap-4">
            <button
                onClick={() => navigate("/register")}
                className="rounded-xl bg-indigo-500 px-6 py-3 font-medium hover:bg-indigo-400 transition">
                Sluit je aan bij de ladder
            </button>

            <button
                onClick={() => navigate("/login")}
                className="rounded-xl border border-white/20 px-6 py-3 hover:bg-white/10 transition">
                Inloggen
            </button>
            </div>
        </section>


        {/* RIGHT — SCOREBOARDS */}
        <aside className= {styles.scoreboardAside}>
            <section className={styles.scoreboardContainer}>
                <h2 className={styles.scoreboardContainerText}>Topspelers</h2>

                <div className={styles.scoreboardCard}>
                    <div className={styles.scoreboardCardTeam}>
                        <span>#1 Lorem</span>
                        <span>Ipsum</span>
                    </div>
                    <div className={styles.scoreboardCardTeam}>
                        <span>#2 Lorem</span>
                        <span>Ipsum</span>
                    </div>
                    <div className={styles.scoreboardCardTeam}>
                        <span>#3 Lorem</span>
                        <span>Ipsum</span>
                    </div>
                </div>
            </section>
            <section className={styles.scoreboardContainer}>
                <h2 className={styles.scoreboardContainerText}>Topwedstrijden</h2>

                <div className={styles.scoreboardCard}>
                    <div className={styles.scoreboardCardMatch}>
                        <span>Lorem vs Ipsum</span>
                        <span>In afwachting</span>
                    </div>
                    <div className={styles.scoreboardCardMatch}>
                        <span>Dolor vs Sit</span>
                        <span>In afwachting</span>
                    </div>
                    <div className={styles.scoreboardCardMatch}>
                        <span>Amet vs Consectetur</span>
                        <span>In afwachting</span>
                    </div>
                </div>
            </section>
        </aside>

        </div>
    )
}

export default Home
