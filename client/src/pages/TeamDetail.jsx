import { useNavigate, useParams } from "react-router-dom";
import { useTeam } from "@/hooks/teams/useTeam.js";
import styles from "@/style/TeamDetail.module.css";
import commonStyles from "@/style/common/Common.module.css";
import panelStyles from "@/style/common/Panel.module.css";
import { useTeamMembers } from "@/hooks/teams/useTeamMembers.js";
import MemberCard from "@/components/team/MemberCard.jsx";
import TeamSettingsLink from "@/components/team/TeamSettingsLink.jsx";
import { useCurrentUserContext } from "@/context/useCurrentUserContext.jsx";
import { useLangContext } from "@/context/useLangContext.jsx";
import { usePageTexts } from "@/hooks/common/usePageTexts.js";
import { useTeamAchievements } from "@/hooks/useLadder.js";

export default function TeamDetail() {
    const { teamId } = useParams();
    const navigate   = useNavigate();
    const { lang } = useLangContext();
    const { currentUser } = useCurrentUserContext();
    const texts = usePageTexts("team_detail", lang);
    const { team, loading, error } = useTeam(teamId);
    const { members, loading: membersLoading, error: membersError, total, reload} = useTeamMembers(teamId);
    const { data: achievementsData } = useTeamAchievements(teamId);

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

            {/* Achievements */}
            {achievementsData?.ladders?.length > 0 && (
                <div className={styles.section}>
                    <h2 className={styles.sectionTitle}>Achievements</h2>
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))", gap: "0.75rem", marginTop: "0.75rem" }}>
                        {achievementsData.ladders.map(row => (
                            <LadderStatCard key={row.ladder_id} row={row} />
                        ))}
                    </div>
                </div>
            )}

            {/* Players */}
            <div className={styles.section}>
                <div className={styles.sectionHeader}>
                    <h2 className={styles.sectionTitle}>{texts.players_title || "Players"}</h2>
                    {total !== null && (
                        <span className={panelStyles.panelCounter}>{total}</span>
                    )}
                </div>

                {membersLoading && (
                    <div className={styles.inlineState}>
                        <div className={styles.spinner} />
                        <span>{texts.loading_players || "Players loading..."}</span>
                    </div>
                )}

                {!membersLoading && membersError && (
                    <div className={styles.inlineState}>
                        <p className={styles.error}>{membersError}</p>
                        <button className={styles.retryBtn} onClick={reload}>{texts.retry || "Retry"}</button>
                    </div>
                )}

                {!membersLoading && !membersError && members.length === 0 && (
                    <p className={commonStyles.muted}>{texts.no_players || "No players in this team yet."}</p>
                )}

                {!membersLoading && !membersError && members.length > 0 && (
                    <ul className={panelStyles.list}>
                        {members.map((member, index) => (
                            <MemberCard key={index} member={member} />
                        ))}
                    </ul>
                )}
            </div>

        </section>
    );
}

/*  Local sub-components  */

function LadderStatCard({ row }) {
    return (
        <div style={{
            border: "1px solid rgba(255,255,255,0.1)",
            borderRadius: "0.75rem",
            padding: "1rem",
            background: "rgba(255,255,255,0.03)",
        }}>
            <p style={{ fontWeight: 600, marginBottom: "0.25rem", fontSize: "0.95rem" }}>{row.ladder_name}</p>
            <p style={{ fontSize: "0.75rem", color: "var(--color-muted, #94a3b8)", marginBottom: "0.75rem" }}>{row.club_name} · Rank #{row.rank ?? "—"}</p>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.5rem", fontSize: "0.8rem" }}>
                <Stat label="Wins" value={row.wins} />
                <Stat label="Rating" value={row.rating} />
                <Stat label="Best streak" value={row.best_win_streak} suffix="🔥" />
                <Stat label="Best #1 reign" value={row.best_rank1_streak} suffix="👑" />
            </div>
        </div>
    );
}

function Stat({ label, value, suffix }) {
    return (
        <div>
            <p style={{ color: "var(--color-muted, #94a3b8)", fontSize: "0.7rem", textTransform: "uppercase", letterSpacing: "0.05em" }}>{label}</p>
            <p style={{ fontWeight: 700, fontSize: "1rem" }}>{value ?? 0}{suffix ? " " + suffix : ""}</p>
        </div>
    );
}

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