import { useNavigate, useParams } from "react-router-dom";
import { useTeam } from "@/hooks/useTeam.js";
import styles from "@/style/TeamDetail.module.css";
import commonStyles from "@/style/common/Common.module.css";
import {useTeamPlayers} from "@/hooks/useTeamPlayers.js";
import PlayerCard from "@/components/team/PlayerCard.jsx";
import TeamSettingsLink from "@/components/team/TeamSettingsLink.jsx";
import { useCurrentUserContext } from "@/context/useCurrentUserContext.js";

export default function TeamDetail() {
    const { teamId } = useParams();
    const navigate   = useNavigate();
    const { currentUser } = useCurrentUserContext();
    const { team, loading, error } = useTeam(teamId);
    const { players, loading: playersLoading, error: playersError, total, reload} = useTeamPlayers(teamId);

    if (loading) {
        return (
            <div className={styles.state}>
                <div className={styles.spinner} />
                <span>Loading team…</span>
            </div>
        );
    }

    if (error) {
        return (
            <div className={styles.state}>
                <p className={styles.error}>{error}</p>
                <button className={styles.backBtn} onClick={() => navigate("/teams")}>
                    &lt;- Back to teams
                </button>
            </div>
        );
    }

    if (!team) return null;

    return (
        <section className={styles.page}>

            {/* Back */}
            <button className={styles.backBtn} onClick={() => navigate("/teams")}>
                &lt;- All Teams
            </button>

            {/* Hero */}
            <div className={styles.hero}>
                <div className={styles.heroAccent} />
                <div className={styles.heroBody} style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "0.75rem" }}>
                    <div>
                        <h1 className={styles.name}>{team.name}</h1>
                        <div className={styles.tags}>
                            <Tag label={team.clubId     ? `Club #${team.clubId}`        : "Independent"} muted={!team.clubId} />
                            <Tag label={team.sportTypeId ? `Sport #${team.sportTypeId}` : "No sport"}    muted={!team.sportTypeId} />
                            <Tag label={`ID: ${team.id}`} muted />
                        </div>
                    </div>
                    <TeamSettingsLink currentUser={currentUser} team={team} size={22} />
                </div>
            </div>

            {/* Details grid */}
            <div className={styles.grid}>
                <InfoCard label="Club" value={team.clubId     ? `#${team.clubId}`      : "—"} />
                <InfoCard label="Sport Type" value={team.sportTypeId ? `#${team.sportTypeId}` : "—"} />
                <InfoCard label="Team ID" value={`#${team.id}`} />
            </div>

            {/* Players */}
            <div className={styles.section}>
                <div className={styles.sectionHeader}>
                    <h2 className={styles.sectionTitle}>Players</h2>
                    {total !== null && (
                        <span className={commonStyles.counter}>{total}</span>
                    )}
                </div>

                {playersLoading && (
                    <div className={styles.inlineState}>
                        <div className={styles.spinner} />
                        <span>Loading players…</span>
                    </div>
                )}

                {!playersLoading && playersError && (
                    <div className={styles.inlineState}>
                        <p className={styles.error}>{playersError}</p>
                        <button className={styles.retryBtn} onClick={reload}>Retry</button>
                    </div>
                )}

                {!playersLoading && !playersError && players.length === 0 && (
                    <p className={commonStyles.muted}>No players in this team yet.</p>
                )}

                {!playersLoading && !playersError && players.length > 0 && (
                    <ul className={commonStyles.list}>
                        {players.map(player => (
                            <PlayerCard key={player.playerId ?? player.id} player={player} />
                        ))}
                    </ul>
                )}
            </div>

        </section>
    );
}

/*  Local sub-components  */

function Tag({ label, muted }) {
    return (
        <span className={`${styles.tag} ${muted ? styles.tagMuted : ""}`}>
            {label}
        </span>
    );
}

function InfoCard({ label, value }) {
    return (
        <div className={styles.infoCard}>
            <p className={styles.infoLabel}>{label}</p>
            <p className={styles.infoValue}>{value}</p>
        </div>
    );
}
