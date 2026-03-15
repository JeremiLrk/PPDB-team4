import { useNavigate } from "react-router-dom"
import background from "@/assets/background.webp"
import styles from "@/style/Home.module.css"
import {usePageTexts} from "@/hooks/usePageTexts.js"
import {useLangContext} from "@/context/useLangContext.js";


function Home() {
    const {lang, setLang } = useLangContext();
    const base_texts = usePageTexts("base", lang);
    const au_texts = usePageTexts("authorization", lang);
    const ladder_texts = usePageTexts("ladder", lang);
    const score_texts = usePageTexts("score", lang);
    const home_texts = usePageTexts("home", lang);

    const navigate = useNavigate()

    return (
        <div className={styles.container}>

        {/* LEFT — LADDER */}
            <aside className={styles.ladderAside}>

                <section className={styles.ladderContainer}>
                    <h2 className={styles.ladderContainerText}>{ladder_texts.ladder}</h2>

                    <div className={styles.ladderCard}>

                        <button
                            onClick={() => navigate("/ladder")}
                            className={styles.ladderButton}
                        >
                            {home_texts.mens_tennis}
                        </button>

                        <button
                            onClick={() => navigate("/ladder")}
                            className={styles.ladderButton}
                        >
                            {home_texts.womens_tennis}
                        </button>

                        <button
                            onClick={() => navigate("/ladder")}
                            className={styles.ladderButton}
                        >
                            {home_texts.padel}
                        </button>

                        <button
                            onClick={() => navigate("/ladder")}
                            className={styles.ladderButton}
                        >
                            {home_texts.juniors}
                        </button>

                        <div className={styles.ladderCard}>

                            <section className="text-center">
                                <h1 className="text-3xl font-semibold tracking-tight">
                                    {home_texts.net_rank}
                                </h1>
                            </section>
                        </div>
                    </div>
                </section>
            </aside>

        {/* CENTER — PICTURE */}
        <section className="text-center">
            <h1 className="text-5xl font-semibold tracking-tight">
                {home_texts.net_rank}
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
                {ladder_texts.join_ladder}
            </button>

            <button
                onClick={() => navigate("/login")}
                className="rounded-xl border border-white/20 px-6 py-3 hover:bg-white/10 transition">
                {au_texts.log_in}
            </button>
            </div>
        </section>


        {/* RIGHT — SCOREBOARDS */}
        <aside className= {styles.scoreboardAside}>
            <section className={styles.scoreboardContainer}>
                <h2 className={styles.scoreboardContainerText}>{score_texts.top_players}</h2>

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
                <h2 className={styles.scoreboardContainerText}>{score_texts.top_matches}</h2>

                <div className={styles.scoreboardCard}>
                    <div className={styles.scoreboardCardMatch}>
                        <span>Lorem vs Ipsum</span>
                        <span>{base_texts.pending}</span>
                    </div>
                    <div className={styles.scoreboardCardMatch}>
                        <span>Dolor vs Sit</span>
                        <span>{base_texts.pending}</span>
                    </div>
                    <div className={styles.scoreboardCardMatch}>
                        <span>Amet vs Consectetur</span>
                        <span>{base_texts.pending}</span>
                    </div>
                </div>
            </section>
        </aside>

        </div>
    )
}

export default Home
