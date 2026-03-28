import { useNavigate, useParams } from "react-router-dom";
import { useTeam } from "@/hooks/useTeam.js";
import styles from "@/style/TeamDetail.module.css";

export default function TeamDetail() {
    const { teamId } = useParams();
    const navigate   = useNavigate();
    const { team, loading, error } = useTeam(teamId);

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
                    ← Back to teams
                </button>
            </div>
        );
    }

    if (!team) return null;

    return (
        <section className={styles.page}>

            {/* Back */}
            <button className={styles.backBtn} onClick={() => navigate("/teams")}>
                ← All Teams
            </button>

            {/* Hero */}
            <div className={styles.hero}>
                <div className={styles.heroAccent} />
                <div className={styles.heroBody}>
                    <h1 className={styles.name}>{team.name}</h1>
                    <div className={styles.tags}>
                        <Tag label={team.clubId     ? `Club #${team.clubId}`        : "Independent"} muted={!team.clubId} />
                        <Tag label={team.sportTypeId ? `Sport #${team.sportTypeId}` : "No sport"}    muted={!team.sportTypeId} />
                        <Tag label={`ID: ${team.id}`} muted />
                    </div>
                </div>
            </div>

            {/* Details grid */}
            <div className={styles.grid}>
                <InfoCard label="Club" value={team.clubId     ? `#${team.clubId}`      : "—"} />
                <InfoCard label="Sport Type" value={team.sportTypeId ? `#${team.sportTypeId}` : "—"} />
                <InfoCard label="Team ID" value={`#${team.id}`} />
            </div>

        </section>
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
