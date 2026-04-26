import { useState, useEffect } from "react"; 
import { useNavigate, useParams } from "react-router-dom";
import tennisBackground from "@/assets/tennis.jpg";
import padelBackground from "@/assets/padel.jpg";
import styles from "@/style/Home.module.css";
import { useLadders } from "@/hooks/useLadders";
import { useTopPlayers } from "@/hooks/useTopPlayers";
import useClub from "@/hooks/useClub";
import { useLangContext } from "@/context/useLangContext.jsx";
import { usePageTexts } from "@/hooks/common/usePageTexts.js";
import { useCurrentUserContext } from "@/context/useCurrentUserContext.jsx";

function getHeroBackground(sport) {
    const normalized = (sport || "").toString().toLowerCase();
    if (normalized.includes("tennis")) return tennisBackground;
    if (normalized.includes("padel")) return padelBackground;
    return null;
}

function ClubHome() {
    const { clubId } = useParams();
    const navigate = useNavigate();
    const { lang } = useLangContext();
    const { currentUser, loadingUser } = useCurrentUserContext();
    
    const [isManager, setIsManager] = useState(false);

    const ladderTexts = usePageTexts("ladder", lang);
    const scoreTexts = usePageTexts("score", lang);
    const clubHomeTexts = usePageTexts("club_home", lang);
    const { ladders, loading } = useLadders(clubId);
    const { club, loading: clubLoading, error: clubError } = useClub(clubId);
    const { players: topPlayers, loading: topLoading } = useTopPlayers(clubId);
    const medals = ["🥇", "🥈", "🥉"];
    const heroBackground = getHeroBackground(club?.sport);

    useEffect(() => {
        const checkManagerStatus = async () => {
            try {
                const response = await fetch(`/api/clubs/${clubId}/is_manager`);
                if (response.ok) {
                    const data = await response.json();
                    setIsManager(data.is_manager);
                }
            } catch (err) {
                console.error("Fout bij checken manager status:", err);
                setIsManager(false);
            }
        };

        if (clubId) {
            checkManagerStatus();
        }
    }, [clubId]);

    const clubHomeStyle = heroBackground
        ? { "--club-home-bg": `url(${heroBackground})` }
        : undefined;

    return (
        <div
            className={styles.page}
            style={clubHomeStyle}
        >
            <div className={styles.pageBackdrop} aria-hidden="true" />
            <div className={styles.pageOverlay} aria-hidden="true" />

            <div className={styles.container}>
                <aside className={styles.ladderAside}>
                    <section className={styles.ladderContainer}>
                        <h2 className={styles.ladderContainerText}>{ladderTexts.ladder || "Ladder"}</h2>

                        <div className={styles.ladderCard}>
                            {loading && <p>{clubHomeTexts.loading_ladders || "Ladders laden..."}</p>}

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

                <main className={styles.clubMain}>
                    <section className={styles.heroPanel}>
                        {clubLoading && <h1>{clubHomeTexts.loading_club || "Club laden..."}</h1>}
                        {clubError && <h1>{clubHomeTexts.error_loading_club || "Fout bij laden van club"}</h1>}
                        {!clubLoading && club && (
                            <>
                                <h1 className={styles.clubTitle}>{club.name}</h1>
                                <p className={styles.clubDescription}>{club.description}</p>

                                {isManager && (
                                    <div className={styles.heroActions}>
                                        <button
                                            onClick={() => navigate(`/clubs/${clubId}/settings`)}
                                            className={styles.manageButton}
                                        >
                                            ⚙️ {clubHomeTexts.manage_club || "Club beheren"}
                                        </button>
                                    </div>
                                )}

                                {!loadingUser && !currentUser ? (
                                    <div className={styles.heroActions}>
                                        <button
                                            onClick={() => navigate("/register")}
                                            className={styles.primaryAction}
                                        >
                                            {ladderTexts.join_ladder || "Sluit je aan bij de ladder"}
                                        </button>

                                        <button
                                            onClick={() => navigate("/login")}
                                            className={styles.secondaryAction}
                                        >
                                            {clubHomeTexts.log_in || "Inloggen"}
                                        </button>
                                    </div>
                                ) : null}
                            </>
                        )}
                    </section>
                </main>

                <aside className={styles.scoreboardAside}>
                    <section className={styles.scoreboardContainer}>
                        <h2 className={styles.scoreboardContainerText}>{scoreTexts.top_players || "Topspelers"}</h2>

                        <div className={styles.scoreboardCard}>
                            {topLoading && <p>Laden...</p>}

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
                </aside>
            </div>
        </div>
    );
}

export default ClubHome;
