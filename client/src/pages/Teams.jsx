// Page container for Teams.

import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import styles from "@/style/Teams.module.css";
import { useTeams } from "@/hooks/teams/useTeams.js";

import { useLangContext } from "@/context/useLangContext.jsx";
import { usePageTexts } from "@/hooks/common/usePageTexts.js";

const SORT_OPTIONS = [
    { value: "id",   label: "By ID" },
    { value: "name", label: "By Name" },
];

const PAGE_SIZE_OPTIONS = [6, 12, 24, 48];

export default function Teams() {
    const navigate = useNavigate();
    const { lang } = useLangContext();
    const texts = usePageTexts("teams", lang);

    const {
        teams, total, loading, error,
        sort, pageSize, hasMore,
        load, loadMore,
    } = useTeams({ pageSize: 12, sort: "name" });

    /*
     Loads the teams list once on mount.
    */
    useEffect(() => { load(); }, []); // eslint-disable-line react-hooks/exhaustive-deps

    function handleSortChange(e) {
        /*
         Reloads the team list using a new sort order.
        */
        load({ sort: e.target.value });
    }

    function handlePageSizeChange(e) {
        /*
         Reloads the team list using a new page size.
        */
        load({ pageSize: Number(e.target.value) });
    }

    return (
        <section className={styles.page}>

            {/* ── Header ── */}
            <div className={styles.header}>
                <div className={styles.titleBlock}>
                    <h1 className={styles.title}>{texts.title || "Teams"}</h1>
                    <p className={styles.subtitle}>
                        {total !== null
                            ? `${total} ${total !== 1 ? (texts.team_plural || "teams") : (texts.team_singular || "team")} ${texts.found || "gevonden"}`
                            : (texts.loading_total || "Laden…")}
                    </p>
                </div>

                <div className={styles.controls}>
                    <span className={styles.controlLabel}>{texts.sort_label || "Sorteren"}</span>
                    <select
                        className={styles.select}
                        value={sort}
                        onChange={handleSortChange}
                        disabled={loading}
                    >
                        {[
                            { value: "id", label: texts.sort_id || "By ID" },
                            { value: "name", label: texts.sort_name || "By name" },
                        ].map(o => (
                            <option key={o.value} value={o.value}>{o.label}</option>
                        ))}
                    </select>

                    <div className={styles.divider} />

                    <span className={styles.controlLabel}>{texts.page_size_label || "Per page"}</span>
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
                <p className={styles.emptyState}>{texts.empty_state || "No teams found."}</p>
            )}

            {/* ── Loading indicator (initial or mid-page) ── */}
            {loading && (
                <div className={styles.stateRow}>
                    <div className={styles.spinner} />
                    <span>{texts.loading_teams || "Teams loading..."}</span>
                </div>
            )}

            {/* ── Footer: counter + load more ── */}
            {teams.length > 0 && (
                <div className={styles.footer}>
                    <span className={styles.counter}>
                        {texts.showing || "Weergegeven"} {teams.length}{total !== null ? ` / ${total}` : ""}
                    </span>

                    <div className={styles.footerRight}>
                        {hasMore && (
                            <button
                                className={styles.loadMoreBtn}
                                onClick={loadMore}
                                disabled={loading}
                            >
                                {loading ? (texts.loading_total || "Loading...") : `${pageSize} ${texts.load_more || "Load more"}`}
                            </button>
                        )}
                    </div>
                </div>
            )}
        </section>
    );
}

function TeamCard({ team, onClick }) {
    /*
     Renders one team card in the public teams grid.
    */
    return (
        <button className={styles.card} onClick={onClick}>
            <div className={styles.cardAccent} />
            <p className={styles.cardName}>{team.name}</p>
            <div className={styles.cardMeta}>
                {team.sportName ? (
                    <span className={styles.badge}>{team.sportName}</span>
                ) : (
                    <span className={`${styles.badge} ${styles.badgeMuted}`}>No sport</span>
                )}
                {team.clubName ? (
                    <span className={styles.badge}>{team.clubName}</span>
                ) : (
                    <span className={`${styles.badge} ${styles.badgeMuted}`}>Independent</span>
                )}
            </div>
        </button>
    );
}
