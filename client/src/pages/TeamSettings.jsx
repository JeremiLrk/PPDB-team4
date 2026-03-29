import { useNavigate, useParams, Link } from "react-router-dom";
import { useState } from "react";
import { useTeam }from "@/hooks/useTeam.js";
import { useTeamPlayers } from "@/hooks/useTeamPlayers.js";
import { useCurrentUserContext }from "@/context/useCurrentUserContext.js";
import AddPlayerButton from "@/components/team/AddPlayerButton.jsx";
import PlayerCard from "@/components/team/PlayerCard.jsx";
import RenameTeamButton from "@/components/team/RenameTeamButton.jsx";
import GearIcon from "@/components/icon/GearIcon.jsx";
import { canManageTeam }from "@/components/team/TeamSettingsLink.jsx";
import styles from "@/style/TeamSettings.module.css";
import commonStyles from "@/style/common/Common.module.css";

export default function TeamSettings() {
    const { teamId }    = useParams();
    const navigate      = useNavigate();
    const { currentUser } = useCurrentUserContext();

    const { team,    loading: teamLoading,    error: teamError    } = useTeam(teamId);
    const { players, loading: playersLoading, error: playersError,
            total,   reload: reloadPlayers, addPlayerLocally} = useTeamPlayers(teamId);

    // Local display name — updated optimistically after rename
    const [displayName, setDisplayName] = useState(null);
    const teamName = displayName ?? team?.name ?? "";

    /* loading */
    if (teamLoading) {
        return (
            <div className={styles.state}>
                <div className={styles.spinner} />
                <span>Loading team…</span>
            </div>
        );
    }

    /* fetch error */
    if (teamError) {
        return (
            <div className={styles.state}>
                <p className={styles.error}>{teamError}</p>
                <button className={styles.backBtn} onClick={() => navigate("/teams")}>
                    &lt;- Back to teams
                </button>
            </div>
        );
    }

    if (!team) return null;

    /* access check */
    if (!currentUser) {
        return (
            <div className={styles.state}>
                <p className={styles.error}>You must be logged in to access this page.</p>
                <Link to="/login" className={styles.backBtn}>→ Log in</Link>
            </div>
        );
    }

    if (!canManageTeam(currentUser, team)) {
        return (
            <div className={styles.state}>
                <p className={styles.error}>Access denied. You do not have permission to manage this team.</p>
                <button className={styles.backBtn} onClick={() => navigate(`/teams/${teamId}`)}>
                    &lt;- Back to team
                </button>
            </div>
        );
    }

    /* main page */
    return (
        <section className={styles.page}>

            {/* Navigation */}
            <div className={styles.breadcrumbs}>
                <button className={styles.backBtn} onClick={() => navigate(`/teams/${teamId}`)}>
                    &lt;- {teamName}
                </button>
                <span className={styles.breadcrumbSep}>/</span>
                <span className={styles.breadcrumbCurrent}>Settings</span>
            </div>

            {/* Hero */}
            <div className={styles.hero}>
                <div className={styles.heroAccent} />
                <div className={styles.heroBody}>
                    <div className={styles.heroTop}>
                        <div>
                            <div className={styles.nameRow}>
                                <h1 className={styles.name}>{teamName}</h1>
                                <RenameTeamButton
                                    teamId={teamId}
                                    currentName={teamName}
                                    onRenamed={t => setDisplayName(t.name)}
                                />
                            </div>
                            <div className={styles.tags}>
                                <Tag label="Settings" accent />
                                <Tag label={team.clubId ? `Club #${team.clubId}` : "Independent"} muted={!team.clubId} />
                                <Tag label={`ID: ${team.id}`} muted />
                            </div>
                        </div>
                        <GearIcon size={32} title="Team settings" className={styles.settingsIcon} />
                    </div>
                </div>
            </div>

            {/* Players section */}
            <div className={styles.section}>
                <div className={styles.sectionHeader}>
                    <div className={styles.sectionTitleRow}>
                        <h2 className={styles.sectionTitle}>Players</h2>
                        {total !== null && (
                            <span className={commonStyles.counter}>{total}</span>
                        )}
                    </div>
                    <AddPlayerButton teamId={teamId} onAdded={reloadPlayers} />
                </div>

                {/* Players loading */}
                {playersLoading && (
                    <div className={styles.inlineState}>
                        <div className={styles.spinner} />
                        <span>Loading players…</span>
                    </div>
                )}

                {/* Players error */}
                {!playersLoading && playersError && (
                    <div className={styles.inlineState}>
                        <p className={styles.error}>{playersError}</p>
                        <button className={styles.retryBtn} onClick={reloadPlayers}>Retry</button>
                    </div>
                )}

                {/* Empty */}
                {!playersLoading && !playersError && players.length === 0 && (
                    <p className={commonStyles.muted}>No players in this team yet. Add some above.</p>
                )}

                {/* List */}
                {!playersLoading && !playersError && players.length > 0 && (
                    <ul className={commonStyles.list}>
                        {players.map(player => (
                            <PlayerCard
                                key={player.playerId ?? player.id}
                                player={player}
                                teamId={teamId}
                                onDeleted={reloadPlayers}
                            />
                        ))}
                    </ul>
                )}
            </div>

        </section>
    );
}

/* Local sub-components */

function Tag({ label, muted, accent }) {
    const cls = [
        styles.tag,
        muted   ? styles.tagMuted   : "",
        accent  ? styles.tagAccent  : "",
    ].filter(Boolean).join(" ");

    return <span className={cls}>{label}</span>;
}
