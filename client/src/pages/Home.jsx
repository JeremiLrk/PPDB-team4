import { useNavigate } from "react-router-dom"
import background from "@/assets/background.webp"
import styles from "@/style/Home.module.css"
import {usePageTexts} from "@/hooks/usePageTexts.js"
import {useLangContext} from "@/context/useLangContext.js";


function Home() {
    const {lang, setLang } = useLangContext();
    const texts = usePageTexts("home", lang);
    const navigate = useNavigate()

    return (
        <div className={styles.container}>

        {/* LEFT — LADDER */}
            <aside className={styles.ladderAside}>

                <section className={styles.ladderContainer}>
                    <h2 className={styles.ladderContainerText}>{texts.hero_title}</h2>

                    <div className={styles.ladderCard}>

                        <button
                            onClick={() => navigate("/ladder")}
                            className={styles.ladderButton}
                        >
                            Men’s Tennis
                        </button>

                        <button
                            onClick={() => navigate("/ladder")}
                            className={styles.ladderButton}
                        >
                            Women’s Tennis
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
                            Juniors
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
        <aside className= {styles.scoreboardAside}>
            <section className={styles.scoreboardContainer}>
                <h2 className={styles.scoreboardContainerText}>Top Players</h2>

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
                <h2 className={styles.scoreboardContainerText}>Top Matches</h2>

                <div className={styles.scoreboardCard}>
                    <div className={styles.scoreboardCardMatch}>
                        <span>Lorem vs Ipsum</span>
                        <span>Pending</span>
                    </div>
                    <div className={styles.scoreboardCardMatch}>
                        <span>Dolor vs Sit</span>
                        <span>Pending</span>
                    </div>
                    <div className={styles.scoreboardCardMatch}>
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
