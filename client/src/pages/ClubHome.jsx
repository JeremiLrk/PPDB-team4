import { useNavigate, useParams } from "react-router-dom";
import background from "@/assets/background.webp";
import styles from "@/style/Home.module.css";
import { useLadders } from "@/hooks/useLadders";
import { useTopPlayers } from "@/hooks/useTopPlayers";
import useClub from "@/hooks/useClub";
import { useLangContext } from "@/context/useLangContext.js";
import { usePageTexts } from "@/hooks/usePageTexts.js";

function ClubHome() {
    const { clubId } = useParams();
    const navigate = useNavigate();
    const { lang } = useLangContext();
    const ladderTexts = usePageTexts("ladder", lang);
    const scoreTexts = usePageTexts("score", lang);
    const baseTexts = usePageTexts("base", lang);
    const clubHomeTexts = usePageTexts("club_home", lang);
    const { ladders, loading } = useLadders(clubId);
    const { club, loading: clubLoading, error: clubError } = useClub(clubId);
    const { players: topPlayers, loading: topLoading } = useTopPlayers(clubId);
    const medals = ["🥇", "🥈", "🥉"];

    return (
        <div className={styles.container}>
            <aside className={styles.ladderAside}>
                <section className={styles.ladderContainer}>
                    <h2 className={styles.ladderContainerText}>{ladderTexts.ladder || "Ladder"}</h2>

                    <div className={styles.ladderCard}>
                        {loading && <p>{clubHomeTexts.loading_ladders || "Loading ladders..."}</p>}

                        {!loading &&
                            ladders.map((ladder) => (
                                <button
                                    key={ladder.id}
                                    onClick={() =>
                                        navigate(`/clubs/${clubId}/ladders/${ladder.id}`)
                                    }
                                    className={styles.ladderButton}
                                >
                                    {ladder.name}
                                </button>
                            ))}
                    </div>
                </section>
            </aside>

            <section className="text-center">
                {clubLoading && <h1>{clubHomeTexts.loading_club || "Loading club..."}</h1>}
                {clubError && <h1>{clubHomeTexts.error_loading_club || "Error loading club"}</h1>}
                {!clubLoading && club && (
                    <h1 className="text-5xl font-semibold tracking-tight">{club.name}</h1>
                )}

                <img src={background} alt="Tennis match" className="mt-6 w-full rounded-2xl" />

                <p className="mt-6 text-lg text-slate-300/70">
                    {clubHomeTexts.tagline || "Compete. Challenge. Climb the ladder."}
                </p>

                <p className="mt-2 text-sm text-slate-400">
                    {clubHomeTexts.subtagline || "The competitive ranking system for tennis and padel clubs."}
                </p>

                <div className="mt-10 flex justify-center gap-4">
                    <button
                        onClick={() => navigate("/register")}
                        className="rounded-xl bg-indigo-500 px-6 py-3 font-medium transition hover:bg-indigo-400"
                    >
                        {ladderTexts.join_ladder || "Join the Ladder"}
                    </button>

                    <button
                        onClick={() => navigate("/login")}
                        className="rounded-xl border border-white/20 px-6 py-3 transition hover:bg-white/10"
                    >
                        {clubHomeTexts.log_in || "Log in"}
                    </button>
                </div>
            </section>

            <aside className={styles.scoreboardAside}>
                <section className={styles.scoreboardContainer}>
                    <h2 className={styles.scoreboardContainerText}>{scoreTexts.top_players || "Top Players"}</h2>

                    <div className={styles.scoreboardCard}>
                        {topLoading && <p>Loading...</p>}

                        {!topLoading &&
                            topPlayers.map((player, index) => (
                                <div key={index} className={styles.scoreboardCardTeam}>
                                    <span>
                                        {medals[index]} {player.name}
                                    </span>
                                    <span>{player.rating}</span>
                                </div>
                            ))}
                    </div>
                </section>
                <section className={styles.scoreboardContainer}>
                    <h2 className={styles.scoreboardContainerText}>{scoreTexts.top_matches || "Top Matches"}</h2>

                    <div className={styles.scoreboardCard}>
                        <div className={styles.scoreboardCardMatch}>
                            <span>Lorem vs Ipsum</span>
                            <span>{baseTexts.pending || "Pending"}</span>
                        </div>
                        <div className={styles.scoreboardCardMatch}>
                            <span>Dolor vs Sit</span>
                            <span>{baseTexts.pending || "Pending"}</span>
                        </div>
                        <div className={styles.scoreboardCardMatch}>
                            <span>Amet vs Consectetur</span>
                            <span>{baseTexts.pending || "Pending"}</span>
                        </div>
                    </div>
                </section>
            </aside>
        </div>
    );
}

export default ClubHome;
