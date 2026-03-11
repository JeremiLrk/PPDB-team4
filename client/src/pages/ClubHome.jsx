import { useNavigate, useParams } from "react-router-dom"
import background from "@/assets/background.webp"
import styles from "@/style/Home.module.css"
import { useLadders } from "@/hooks/useLadders"
import { useTopPlayers } from "@/hooks/useTopPlayers"
import useClub from "@/hooks/useClub"


function ClubHome() {
    const { clubId } = useParams()
    const navigate = useNavigate()
    const { ladders, loading } = useLadders(clubId)
    const { club, loading: clubLoading, error: clubError } = useClub(clubId)
    const { players: topPlayers, loading: topLoading } = useTopPlayers(clubId)
    const medals = ["🥇","🥈","🥉"]

    return (
        <div className={styles.container}>

        {/* LEFT — LADDER */}
            <aside className={styles.ladderAside}>

                <section className={styles.ladderContainer}>
                    <h2 className={styles.ladderContainerText}>Ladders</h2>

                    <div className={styles.ladderCard}>

                        {loading && <p>Loading ladders...</p>}

                        {!loading && ladders.map((ladder) => (
                            <button
                                key={ladder.id}
                                onClick={() => navigate(`/clubs/${clubId}/ladders`)}
                                className={styles.ladderButton}
                            >
                                {ladder.name}
                            </button>
                        ))}

                        <div className={styles.ladderCard}>
                        </div>
                    </div>
                </section>
            </aside>

        {/* CENTER — PICTURE */}
        <section className="text-center">
            {clubLoading && <h1>Loading club...</h1>}
            {clubError && <h1>Error loading club</h1>}
            {!clubLoading && club && (
                <h1 className="text-5xl font-semibold tracking-tight">
                    {club.name}
                </h1>
            )}

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
                {topLoading && <p>Loading...</p>}

                {!topLoading && topPlayers.map((player, index) => (
                    <div key={index} className={styles.scoreboardCardTeam}>
                        <span>{medals[index]} {player.name}</span>
                        <span>{player.rating}</span>
                    </div>
                ))}
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

export default ClubHome;
