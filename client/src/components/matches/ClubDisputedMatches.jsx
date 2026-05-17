// Match workflow UI component for ClubDisputedMatches.

import styles from "@/style/ClubSettings.module.css";
import { useDisputedMatches } from "@/hooks/matches/useDisputedMatches.js";
import DisputedMatchCard from "@/components/club_settings/DisputedMatchCard.jsx";

/**
 * ClubDisputedMatches
 *
 * Renders the list of matches in "disputed" score_status that the current user
 * can adjudicate. The visibility logic mirrors the server-side route
 * GET /api/matches/disputed:
 *
 *   - Administrator      -> sees all disputed matches
 *   - ClubOwner          -> sees disputed matches for ladders owned by their club
 *   - TeamManager / anon -> API returns 403; this component renders an
 *                           "insufficient permissions" notice instead
 *
 * Intended to live as a sibling panel to the other ClubSettings tabs.
 * Receives `texts` and `clubId` from the same ClubSettings context as all
 * other sub-components (ClubOverview, ClubMembers, etc.).
 *
 * @param {{ clubId: string|number, texts: object }} props
 */
export default function ClubDisputedMatches({ clubId, texts = {} }) {
    const { matches, total, loading, error, forbidden, reload } = useDisputedMatches(clubId);

    if (forbidden) {
        /*
         Shows the access-denied state instead of the disputed match list.
        */
        return (
            <div className={`${styles.contentGrid} ${styles.contentFade}`}>
                <article
                    className={styles.panel}
                    style={{ gridColumn: "1 / -1", display: "grid", gap: "0.6rem" }}
                >
                    <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
                        {/* Lock icon (inline SVG, no external dependency) */}
                        <svg
                            xmlns="http://www.w3.org/2000/svg"
                            width="20" height="20"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            style={{ color: "var(--text-secondary)", flexShrink: 0 }}
                            aria-hidden="true"
                        >
                            <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                            <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                        </svg>
                        <h3 className={styles.panelTitle}>
                            {texts.disputed_title || "Disputed matches"}
                        </h3>
                    </div>

                    <p className={styles.muted}>
                        {texts.disputed_forbidden
                            || "You do not have permission to view or adjudicate disputed matches. Only club owners and administrators can access this section."}
                    </p>
                </article>
            </div>
        );
    }

    // --- Loading state ---
    if (loading) {
        return (
            <div className={`${styles.contentGrid} ${styles.contentFade}`}>
                <article className={styles.panel} style={{ gridColumn: "1 / -1" }}>
                    <h3 className={styles.panelTitle}>
                        {texts.disputed_title || "Disputed matches"}
                    </h3>
                    <p className={styles.muted} style={{ marginTop: "0.5rem" }}>
                        {texts.loading || "Loading..."}
                    </p>
                </article>
            </div>
        );
    }

    // --- Error state ---
    if (error) {
        return (
            <div className={`${styles.contentGrid} ${styles.contentFade}`}>
                <article className={styles.panel} style={{ gridColumn: "1 / -1" }}>
                    <h3 className={styles.panelTitle}>
                        {texts.disputed_title || "Disputed matches"}
                    </h3>
                    <p className={styles.warning} style={{ marginTop: "0.5rem" }}>
                        {error}
                    </p>
                    <button
                        type="button"
                        className={styles.submitButton}
                        onClick={reload}
                        style={{ marginTop: "0.75rem", width: "fit-content" }}
                    >
                        {texts.retry || "Retry"}
                    </button>
                </article>
            </div>
        );
    }

    // --- Main view ---
    return (
        <div className={`${styles.contentGrid} ${styles.contentFade}`}>
            <article className={styles.panel} style={{ gridColumn: "1 / -1" }}>
                {/* Header row */}
                <div className={styles.panelTopRow} style={{ marginBottom: "0.75rem" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "0.55rem" }}>
                        {/* Alert triangle icon */}
                        <svg
                            xmlns="http://www.w3.org/2000/svg"
                            width="20" height="20"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            style={{ color: "#fca5a5", flexShrink: 0 }}
                            aria-hidden="true"
                        >
                            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                            <line x1="12" y1="9" x2="12" y2="13" />
                            <line x1="12" y1="17" x2="12.01" y2="17" />
                        </svg>
                        <h3 className={styles.panelTitle}>
                            {texts.disputed_title || "Disputed matches"}
                        </h3>
                    </div>

                    {/* Count badge */}
                    {total > 0 && (
                        <span style={{
                            marginLeft: "auto",
                            fontSize: "0.78rem",
                            fontWeight: 700,
                            padding: "0.22rem 0.6rem",
                            borderRadius: "999px",
                            border: "1px solid rgba(239,68,68,0.42)",
                            color: "#fca5a5",
                            background: "rgba(127,29,29,0.28)",
                        }}>
                            {total}
                        </span>
                    )}

                    <button
                        type="button"
                        onClick={reload}
                        style={{
                            marginLeft: total > 0 ? "0.5rem" : "auto",
                            background: "none",
                            border: "1px solid var(--muted-border)",
                            borderRadius: "0.45rem",
                            color: "var(--text-secondary)",
                            cursor: "pointer",
                            fontSize: "0.78rem",
                            padding: "0.22rem 0.6rem",
                            transition: "border-color 0.15s",
                        }}
                    >
                        {texts.refresh || "Refresh"}
                    </button>
                </div>

                {/* Description */}
                <p className={styles.muted} style={{ marginBottom: "1rem", fontSize: "0.88rem" }}>
                    {texts.disputed_description
                        || "These matches have conflicting score submissions from both teams. As a club owner or administrator, you can review the difference and submit the decisive score."}
                </p>

                {/* Empty state */}
                {matches.length === 0 && (
                    <div style={{
                        padding: "1.8rem",
                        textAlign: "center",
                        border: "1px dashed var(--muted-border)",
                        borderRadius: "0.85rem",
                        background: "rgba(255,255,255,0.02)",
                    }}>
                        <p className={styles.muted} style={{ fontSize: "0.9rem" }}>
                            {texts.no_disputed || "No disputed matches at this time."}
                        </p>
                    </div>
                )}

                {/* Match list */}
                {matches.length > 0 && (
                    <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "grid", gap: "0.75rem" }}>
                        {matches.map(match => (
                            <DisputedMatchCard
                                key={match.id}
                                match={match}
                                texts={texts}
                            />
                        ))}
                    </ul>
                )}
            </article>
        </div>
    );
}
