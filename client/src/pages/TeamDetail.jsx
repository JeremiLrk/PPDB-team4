import { useNavigate, useParams } from "react-router-dom";
import { useTeam } from "@/hooks/teams/useTeam.js";
import styles from "@/style/TeamDetail.module.css";
import commonStyles from "@/style/common/Common.module.css";
import panelStyles from "@/style/common/Panel.module.css";
import {useTeamPlayers} from "@/hooks/teams/useTeamPlayers.js";
import PlayerCard from "@/components/team/PlayerCard.jsx";
import TeamSettingsLink from "@/components/team/TeamSettingsLink.jsx";
import { useCurrentUserContext } from "@/context/useCurrentUserContext.jsx";
import { useLangContext } from "@/context/useLangContext.jsx";
import { usePageTexts } from "@/hooks/common/usePageTexts.js";

export default function TeamDetail() {
    const { teamId } = useParams();
    const navigate   = useNavigate();
    const { lang } = useLangContext();
    const { currentUser } = useCurrentUserContext();
    const texts = usePageTexts("team_detail", lang);
    const { team, loading, error } = useTeam(teamId);
    const { players, loading: playersLoading, error: playersError, total, reload} = useTeamPlayers(teamId);

    if (loading) {
        return (
            <div className={styles.state}>
                <div className={styles.spinner} />
                <span>{texts.loading_team || "Team loading..."}</span>
            </div>
        );
    }

    if (error) {
        return (
            <div className={styles.state}>
                <p className={styles.error}>{error}</p>
                <button className={styles.backBtn} onClick={() => navigate("/teams")}>
                    &lt;- {texts.back_to_teams || "Back to teams"}
                </button>
            </div>
        );
    }

    if (!team) return null;

    return (
        <section className={styles.page}>

            {/* Back */}
            <button className={styles.backBtn} onClick={() => navigate("/teams")}>
                &lt;- {texts.back_to_teams || "Back to teams"}
            </button>

            {/* Hero */}
            <div className={styles.hero}>
                <div className={styles.heroAccent} />
                <div className={styles.heroBody} style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "0.75rem" }}>
                    <div>
                        <h1 className={styles.name}>{team.name}</h1>
                        <div className={styles.tags}>
                            <Tag label={team.clubName ? team.clubName : "Independent"} muted={!team.clubId} />
                            <Tag label={team.sportName ?  `${team.sportName || "Sport #"+team.sportTypeId}` : "No sport"} muted={!team.sportTypeId} />
                            <Tag label={`ID: ${team.id}`} muted />
                        </div>
                    </div>
                    <TeamSettingsLink currentUser={currentUser} team={team} size={22} />
                </div>
            </div>

            {/* Details grid */}
            <div className={styles.grid}>
                <InfoCard label={texts.club_label || "Club"} value={team.clubName    ?? "—"} />
                <InfoCard label={texts.sport_label || "Sport"} value={team.sportName   ?? "—"}/>
                <InfoCard label={texts.team_id_label || "Team ID"} value={`#${team.id}`} />
            </div>

            {/* Players */}
            <div className={styles.section}>
                <div className={styles.sectionHeader}>
                    <h2 className={styles.sectionTitle}>{texts.players_title || "Players"}</h2>
                    {total !== null && (
                        <span className={panelStyles.panelCounter}>{total}</span>
                    )}
                </div>

                {playersLoading && (
                    <div className={styles.inlineState}>
                        <div className={styles.spinner} />
                        <span>{texts.loading_players || "Players loading..."}</span>
                    </div>
                )}

                {!playersLoading && playersError && (
                    <div className={styles.inlineState}>
                        <p className={styles.error}>{playersError}</p>
                        <button className={styles.retryBtn} onClick={reload}>{texts.retry || "Retry"}</button>
                    </div>
                )}

                {!playersLoading && !playersError && players.length === 0 && (
                    <p className={commonStyles.muted}>{texts.no_players || "No players in this team yet."}</p>
                )}

                {!playersLoading && !playersError && players.length > 0 && (
                    <ul className={panelStyles.list}>
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