import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import styles from "@/style/Teams.module.css";
import { useTeams } from "@/hooks/teams/useTeams.js";

const SORT_OPTIONS = [
    { value: "id",   label: "By ID" },
    { value: "name", label: "By Name" },
];

const PAGE_SIZE_OPTIONS = [6, 12, 24, 48];

export default function Teams() {
    const navigate = useNavigate();

    const {
        teams, total, loading, error,
        sort, pageSize, hasMore,
        load, loadMore,
    } = useTeams({ pageSize: 12, sort: "name" });

    // Initial load
    useEffect(() => { load(); }, []); // eslint-disable-line react-hooks/exhaustive-deps

    function handleSortChange(e) {
        load({ sort: e.target.value });
    }

    function handlePageSizeChange(e) {
        load({ pageSize: Number(e.target.value) });
    }

    return (
        <section className={styles.page}>

            {/* ── Header ── */}
            <div className={styles.header}>
                <div className={styles.titleBlock}>
                    <h1 className={styles.title}>Teams</h1>
                    <p className={styles.subtitle}>
                        {total !== null
                            ? `${total} team${total !== 1 ? "s" : ""} found`
                            : "Loading…"}
                    </p>
                </div>

                <div className={styles.controls}>
                    <span className={styles.controlLabel}>Sort</span>
                    <select
                        className={styles.select}
                        value={sort}
                        onChange={handleSortChange}
                        disabled={loading}
                    >
                        {SORT_OPTIONS.map(o => (
                            <option key={o.value} value={o.value}>{o.label}</option>
                        ))}
                    </select>

                    <div className={styles.divider} />

                    <span className={styles.controlLabel}>Per load</span>
                    <select
                        className={styles.select}
                        value={pageSize}
                        onChange={handlePageSizeChange}
                        disabled={loading}
                    >
                        {PAGE_SIZE_OPTIONS.map(n => (
                            <option key={n} value={n}>{n}</option>
                        ))}
                    </select>
                </div>
            </div>

            {/* ── Error ── */}
            {error && <p className={styles.error}>{error}</p>}

            {/* ── Grid ── */}
            {teams.length > 0 && (
                <div className={styles.grid}>
                    {teams.map(team => (
                        <TeamCard
                            key={team.id}
                            team={team}
                            onClick={() => navigate(`/teams/${team.id}`)}
                        />
                    ))}
                </div>
            )}

            {/* ── Empty ── */}
            {!loading && !error && teams.length === 0 && (
                <p className={styles.emptyState}>No teams found.</p>
            )}

            {/* ── Loading indicator (initial or mid-page) ── */}
            {loading && (
                <div className={styles.stateRow}>
                    <div className={styles.spinner} />
                    <span>Loading teams…</span>
                </div>
            )}

            {/* ── Footer: counter + load more ── */}
            {teams.length > 0 && (
                <div className={styles.footer}>
                    <span className={styles.counter}>
                        Showing {teams.length}{total !== null ? ` of ${total}` : ""}
                    </span>

                    <div className={styles.footerRight}>
                        {hasMore && (
                            <button
                                className={styles.loadMoreBtn}
                                onClick={loadMore}
                                disabled={loading}
                            >
                                {loading ? "Loading…" : `Load ${pageSize} more`}
                            </button>
                        )}
                    </div>
                </div>
            )}
        </section>
    );
}

function TeamCard({ team, onClick }) {
    return (
        <button className={styles.card} onClick={onClick}>
            <div className={styles.cardAccent} />
            <p className={styles.cardName}>{team.name}</p>
            <div className={styles.cardMeta}>
                {team.sportTypeId ? (
                    <span className={styles.badge}>#{team.sportTypeId}</span>
                ) : (
                    <span className={`${styles.badge} ${styles.badgeMuted}`}>No sport</span>
                )}
                {team.clubId ? (
                    <span className={styles.badge}>Club #{team.clubId}</span>
                ) : (
                    <span className={`${styles.badge} ${styles.badgeMuted}`}>Independent</span>
                )}
            </div>
        </button>
    );
}
