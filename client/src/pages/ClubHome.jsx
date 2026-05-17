// Page container for ClubHome.

import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import styles from "@/style/Home.module.css";
import { useLangContext } from "@/context/useLangContext.jsx";
import { usePageTexts } from "@/hooks/common/usePageTexts.js";
import { useCurrentUserContext } from "@/context/useCurrentUserContext.jsx";
import { useClubHomeSummary } from "@/hooks/useClubHomeSummary";

function ClubHome() {
    const { clubId } = useParams();
    const navigate = useNavigate();
    const { lang } = useLangContext();
    const { currentUser, loadingUser } = useCurrentUserContext();
    /*
     Owns the club-home summary state and the manager flag.
    */

    const [isManager, setIsManager] = useState(false);
    /*
     Keeps the match lists capped so the page stays compact on load.
    */
    const [upcomingVisible, setUpcomingVisible] = useState(3);
    const [resultsVisible, setResultsVisible] = useState(3);

    const ladderTexts = usePageTexts("ladder", lang);
    const clubHomeTexts = usePageTexts("club_home", lang);
    const { summary, loading, error } = useClubHomeSummary(clubId);

    const club = summary.club;
    const ladders = summary.ladders;
    const performers = summary.performers;
    const upcomingMatches = summary.upcomingMatches;
    const latestResults = summary.latestResults;
    /*
     Reloads the manager flag when the club route changes.
    */

    useEffect(() => {
        const checkManagerStatus = async () => {
            /*
             Checks whether the current user can manage this club.
            */
            try {
                /*
                 Manager access is fetched separately so the hero can show the
                 settings CTA without waiting for the full club summary payload.
                */
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
    return (
        <div className={styles.page}>
            <div className={styles.pageBackdrop} aria-hidden="true" />
            <div className={styles.pageOverlay} aria-hidden="true" />

            <div className={styles.container}>
                <aside className={`${styles.panel} ${styles.laddersPanel}`}>
                    <div className={styles.panelHeader}>
                        <h2 className={styles.panelTitle}>{ladderTexts.ladder || "Ladders"}</h2>
                    </div>

                    <div className={styles.panelBody}>
                        {loading && <p className={styles.muted}>{clubHomeTexts.loading_summary || "Loading overview..."}</p>}
                        {!loading && !error && ladders.length === 0 && (
                            <p className={styles.muted}>{clubHomeTexts.no_ladders || "No ladders available yet."}</p>
                        )}
                        {!loading && ladders.length > 0 && (
                            <div className={styles.linkList}>
                                {ladders.map((ladder) => (
                                    <button
                                        key={ladder.id}
                                        onClick={() => navigate(`/clubs/${clubId}/ladders/${ladder.id}`)}
                                        className={styles.linkCard}
                                    >
                                        <span className={styles.linkLabel}>{ladder.name}</span>
                                        <span className={styles.linkArrow}>›</span>
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>
                </aside>

                <section className={`${styles.heroPanel} ${styles.heroGridCard}`}>
                    <div className={styles.heroEyebrow}>
                        {club?.sport || clubHomeTexts.club_label || "Club"}
                    </div>

                    {loading && !club && (
                        <h1 className={styles.heroTitle}>{clubHomeTexts.loading_club || "Loading club..."}</h1>
                    )}

                    {error && (
                        <h1 className={styles.heroTitle}>{clubHomeTexts.error_loading_club || "Error loading club"}</h1>
                    )}

                    {!loading && club && (
                        <>
                            <h1 className={styles.heroTitle}>{club.name}</h1>
                            <p className={styles.heroSubtitle}>
                                {club.description || clubHomeTexts.subtagline || "The competitive ranking system for clubs."}
                            </p>

                            <div className={styles.heroActions}>
                                {isManager && (
                                    <button
                                        onClick={() => navigate(`/clubs/${clubId}/settings`)}
                                        className={styles.primaryAction}
                                    >
                                        {clubHomeTexts.manage_club || "Manage club"}
                                    </button>
                                )}

                                {!loadingUser && !currentUser ? (
                                    <>
                                        <button
                                            onClick={() => navigate("/register")}
                                            className={styles.primaryAction}
                                        >
                                            {ladderTexts.join_ladder || "Join the ladder"}
                                        </button>

                                        <button
                                            onClick={() => navigate("/login")}
                                            className={styles.secondaryAction}
                                        >
                                            {clubHomeTexts.log_in || "Log in"}
                                        </button>
                                    </>
                                ) : null}
                            </div>
                        </>
                    )}
                </section>

                <aside className={`${styles.panel} ${styles.performersPanel}`}>
                    <div className={styles.panelHeader}>
                        <h2 className={styles.panelTitle}>
                            {clubHomeTexts.performers_title || "Top performers"}
                        </h2>
                    </div>

                    <div className={styles.panelBody}>
                        {loading && <p className={styles.muted}>{clubHomeTexts.loading_summary || "Loading overview..."}</p>}

                        {!loading && !error && performers.length === 0 && (
                            <p className={styles.muted}>{clubHomeTexts.no_performers || "No performers available yet."}</p>
                        )}

                        {!loading && performers.length > 0 && (
                            <div className={styles.performerList}>
                                {performers.map((performer, index) => (
                                    <article key={performer.id ?? `${performer.name}-${index}`} className={styles.performerCard}>
                                        <div className={styles.rankBadge}>{index + 1}</div>
                                        <div className={styles.performerMeta}>
                                            <p className={styles.performerName}>{performer.name}</p>
                                            <p className={styles.performerLadder}>{performer.ladderName || clubHomeTexts.performer_label || "Club performer"}</p>
                                        </div>
                                        <div className={styles.performerRating}>
                                            <span>{performer.rating}</span>
                                            <small>{clubHomeTexts.rating_label || "Rating"}</small>
                                        </div>
                                    </article>
                                ))}
                            </div>
                        )}
                    </div>
                </aside>

                <section className={`${styles.panel} ${styles.matchesPanel} ${styles.upcomingPanel}`}>
                    <div className={styles.panelHeader}>
                        <h2 className={styles.panelTitle}>
                            {clubHomeTexts.upcoming_title || "Upcoming matches"}
                        </h2>
                    </div>

                    <div className={styles.panelBody}>
                        {!loading && !error && upcomingMatches.length === 0 && (
                            <p className={styles.muted}>{clubHomeTexts.no_upcoming_matches || "No upcoming matches scheduled."}</p>
                        )}

                        {!loading && upcomingMatches.length > 0 && (
                            <div className={styles.matchList}>
                                {upcomingMatches.slice(0, upcomingVisible).map((match) => (
                                    <article key={match.id} className={styles.matchCard}>
                                        <div className={styles.matchTeams}>
                                            <div className={styles.matchTeam}>{match.team1Name}</div>
                                            <div className={styles.matchTeam}>{match.team2Name}</div>
                                        </div>

                                        <div className={styles.matchSeparator}>
                                            <span className={styles.matchSeparatorLine} aria-hidden="true" />
                                            <span className={styles.matchVs}>vs</span>
                                            <span className={styles.matchSeparatorLine} aria-hidden="true" />
                                        </div>

                                        <div className={styles.matchMetaCenter}>
                                            <span className={styles.matchLadderPill}>{match.ladderName || clubHomeTexts.ladder_label || "Ladder"}</span>
                                        </div>
                                    </article>
                                ))}

                                {/* Load in batches so the club page can show more fixtures without becoming too tall. */}
                                {upcomingVisible < upcomingMatches.length && (
                                    <button
                                        type="button"
                                        className={styles.loadMoreButton}
                                        onClick={() => setUpcomingVisible((count) => Math.min(count + 3, upcomingMatches.length))}
                                    >
                                        {clubHomeTexts.load_more || "Load more"}
                                    </button>
                                )}
                            </div>
                        )}
                    </div>
                </section>

                <section className={`${styles.panel} ${styles.matchesPanel} ${styles.resultsPanel}`}>
                    <div className={styles.panelHeader}>
                        <h2 className={styles.panelTitle}>
                            {clubHomeTexts.latest_results_title || "Latest results"}
                        </h2>
                    </div>

                    <div className={styles.panelBody}>
                        {!loading && !error && latestResults.length === 0 && (
                            <p className={styles.muted}>{clubHomeTexts.no_latest_results || "No latest results available."}</p>
                        )}

                        {!loading && latestResults.length > 0 && (
                            <div className={styles.matchList}>
                                {latestResults.slice(0, resultsVisible).map((match) => (
                                    <article key={match.id} className={styles.resultCard}>
                                        <div className={styles.resultTeams}>
                                            <div className={styles.matchTeam}>{match.team1Name}</div>
                                            <div className={styles.resultScore}>
                                                <span>{match.scoreTeam1 ?? "-"}</span>
                                                <span className={styles.resultDash}>-</span>
                                                <span>{match.scoreTeam2 ?? "-"}</span>
                                            </div>
                                            <div className={styles.matchTeam}>{match.team2Name}</div>
                                        </div>

                                        <div className={styles.matchMetaCenter}>
                                            <span className={styles.matchLadderPill}>{match.ladderName || clubHomeTexts.ladder_label || "Ladder"}</span>
                                        </div>
                                    </article>
                                ))}

                                {/* Results use the same incremental reveal pattern as upcoming matches. */}
                                {resultsVisible < latestResults.length && (
                                    <button
                                        type="button"
                                        className={styles.loadMoreButton}
                                        onClick={() => setResultsVisible((count) => Math.min(count + 3, latestResults.length))}
                                    >
                                        {clubHomeTexts.load_more || "Load more"}
                                    </button>
                                )}
                            </div>
                        )}
                    </div>
                </section>
            </div>
        </div>
    );
}

export default ClubHome;
