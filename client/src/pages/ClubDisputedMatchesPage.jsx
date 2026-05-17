import { useNavigate, useParams } from "react-router-dom";
import { useState } from "react";

import { useClubSettings } from "@/hooks/useClubSettings.js";
import { useDisputedMatches } from "@/hooks/matches/useDisputedMatches.js";
import { useLangContext } from "@/context/useLangContext.jsx";
import { usePageTexts } from "@/hooks/common/usePageTexts.js";
import { useThemeContext } from "@/context/useThemeContext.jsx";

import ClubSidebar from "@/components/club_settings/ClubSidebar.jsx";
import styles from "@/style/ClubSettings.module.css";

/**
 * ClubDisputedMatchesPage
 *
 * A dedicated full-page route (/clubs/:clubId/settings/disputed) for reviewing
 * and adjudicating disputed matches. Uses the same ClubSettings shell
 * (sidebar + workspace) so navigation and context remain identical to other
 * settings pages. The content layout mirrors ClubLadders: a two-column
 * contentGrid with an action panel on the left and a live list on the right.
 *
 * Permission model mirrors the server:
 *   - Administrator / ClubOwner of the ladder's club -> full access
 *   - Anyone else -> forbidden notice replaces the workspace
 */
export default function ClubDisputedMatchesPage() {
    const { clubId }    = useParams();
    const navigate      = useNavigate();
    const { lang }      = useLangContext();
    const texts         = usePageTexts("club_settings", lang);

    // Pull shared club data (same hook as ClubSettings) so sidebar has the
    // same context as all other settings tabs.
    const settings = useClubSettings(clubId, texts);
    const { theme } = useThemeContext();
    const isLight = theme === "light";

    // Disputed-match data
    const {
        matches,
        total,
        loading:   disputedLoading,
        error:     disputedError,
        forbidden,
        reload,
    } = useDisputedMatches(clubId);

    // Which match is selected for detail view (left panel)
    const [selectedId, setSelectedId] = useState(null);
    const selectedMatch = matches.find(m => m.id === selectedId) ?? null;

    // Score adjudication form state
    const [adjScore, setAdjScore]         = useState({ team1: "", team2: "" });
    const [adjSubmitting, setAdjSubmitting] = useState(false);
    const [adjMessage, setAdjMessage]     = useState(null);

    // -----------------------------------------------------------------------
    // Loading skeleton while club data arrives
    // -----------------------------------------------------------------------
    if (!texts.sidebar_title || settings.loading) {
        return (
            <div className={styles.loading}>
                {texts.loading || "Loading..."}
            </div>
        );
    }

    // -----------------------------------------------------------------------
    // Adjudication submit handler
    // -----------------------------------------------------------------------
    async function submitAdjudication(matchId) {
        const s1 = parseInt(adjScore.team1, 10);
        const s2 = parseInt(adjScore.team2, 10);

        if (isNaN(s1) || isNaN(s2) || s1 < 0 || s2 < 0) {
            setAdjMessage({ type: "error", text: "Enter valid non-negative scores for both teams." });
            return;
        }

        setAdjSubmitting(true);
        setAdjMessage(null);

        try {
            const res = await fetch(`/api/matches/${matchId}/score`, {
                method: "POST",
                credentials: "include",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ score_team1: s1, score_team2: s2 }),
            });

            const data = await res.json();

            if (!res.ok) {
                throw new Error(data?.message || "Could not submit score.");
            }

            setAdjMessage({
                type: "success",
                text: data.finalized
                    ? `Match finalized. Final score: ${data.resolvedScore?.scoreTeam1} - ${data.resolvedScore?.scoreTeam2}.`
                    : "Score submitted.",
            });

            // Refresh the list so resolved matches disappear
            await reload();
            setSelectedId(null);
            setAdjScore({ team1: "", team2: "" });
        } catch (err) {
            setAdjMessage({ type: "error", text: err.message });
        } finally {
            setAdjSubmitting(false);
        }
    }

    // -----------------------------------------------------------------------
    // Render
    // -----------------------------------------------------------------------
    return (
        <section className={`${styles.shell} ${isLight ? styles.light : ""}`}>

            {/* Sidebar — same as ClubSettings, "disputed" is the active tab */}
            <ClubSidebar
                activeTab="disputed"
                onTabChange={(tab) => {
                    if (tab === "disputed") return;
                    navigate(`/clubs/${clubId}/settings`);
                    // The ClubSettings page defaults activeTab to "general";
                    // deep-linking per tab is handled there via its own state.
                }}
                texts={texts}
                clubId={clubId}
            />

            {/* Main workspace */}
            <div className={styles.settings}>
                <div className={styles.workspace}>

                    {/* Page header */}
                    <header className={styles.workspaceHeader}>
                        <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
                            {/* Alert triangle icon */}
                            <svg
                                xmlns="http://www.w3.org/2000/svg"
                                width="22" height="22"
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
                                <line x1="12" y1="9"  x2="12"   y2="13" />
                                <line x1="12" y1="17" x2="12.01" y2="17" />
                            </svg>
                            <h2 className={styles.workspaceTitle}>
                                {texts.tab_disputed || "Disputed matches"}
                            </h2>
                            {total > 0 && (
                                <span style={{
                                    fontSize: "0.76rem",
                                    fontWeight: 700,
                                    padding: "0.18rem 0.55rem",
                                    borderRadius: "999px",
                                    border: "1px solid rgba(239,68,68,0.42)",
                                    color: "#fca5a5",
                                    background: "rgba(127,29,29,0.28)",
                                }}>
                                    {total}
                                </span>
                            )}
                        </div>
                        <p className={styles.workspaceSubtitle}>
                            {texts.disputed_description
                                || "Matches where both teams submitted conflicting scores. Select a match to review the difference and submit the decisive score."}
                        </p>
                    </header>

                    {/* ---- FORBIDDEN ---- */}
                    {forbidden && (
                        <ForbiddenNotice texts={texts} onBack={() => navigate(`/clubs/${clubId}/settings`)} />
                    )}

                    {/* ---- LOADING ---- */}
                    {!forbidden && disputedLoading && (
                        <div className={`${styles.contentGrid} ${styles.contentFade}`}>
                            <article className={styles.panel} style={{ gridColumn: "1 / -1" }}>
                                <p className={styles.muted}>{texts.loading || "Loading..."}</p>
                            </article>
                        </div>
                    )}

                    {/* ---- ERROR ---- */}
                    {!forbidden && !disputedLoading && disputedError && (
                        <div className={`${styles.contentGrid} ${styles.contentFade}`}>
                            <article className={styles.panel} style={{ gridColumn: "1 / -1" }}>
                                <p className={styles.warning}>{disputedError}</p>
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
                    )}

                    {/* ---- MAIN CONTENT ---- */}
                    {!forbidden && !disputedLoading && !disputedError && (
                        <div className={`${styles.contentGrid} ${styles.contentFade}`}>

                            {/* LEFT — detail / adjudication panel */}
                            <article className={styles.panel}>
                                <div className={styles.panelScroll}>
                                    {!selectedMatch ? (
                                        <EmptyDetailPanel texts={texts} hasMatches={matches.length > 0} />
                                    ) : (
                                        <AdjudicationPanel
                                            match={selectedMatch}
                                            adjScore={adjScore}
                                            setAdjScore={setAdjScore}
                                            adjSubmitting={adjSubmitting}
                                            adjMessage={adjMessage}
                                            onSubmit={submitAdjudication}
                                            onClear={() => {
                                                setSelectedId(null);
                                                setAdjMessage(null);
                                                setAdjScore({ team1: "", team2: "" });
                                            }}
                                            texts={texts}
                                        />
                                    )}
                                </div>
                            </article>

                            {/* RIGHT — disputed matches list */}
                            <article className={styles.panel}>
                                <div className={styles.panelTopRow} style={{ marginBottom: "0.65rem" }}>
                                    <h3 className={styles.panelTitle}>
                                        {texts.disputed_queue_title || "Dispute queue"}
                                    </h3>
                                    <button
                                        type="button"
                                        onClick={reload}
                                        style={{
                                            marginLeft: "auto",
                                            background: "none",
                                            border: "1px solid var(--muted-border)",
                                            borderRadius: "0.45rem",
                                            color: "var(--text-secondary)",
                                            cursor: "pointer",
                                            fontSize: "0.78rem",
                                            padding: "0.22rem 0.6rem",
                                        }}
                                    >
                                        {texts.refresh || "Refresh"}
                                    </button>
                                </div>

                                <div className={styles.panelScroll}>
                                    {matches.length === 0 ? (
                                        <div style={{
                                            padding: "2rem",
                                            textAlign: "center",
                                            border: "1px dashed var(--muted-border)",
                                            borderRadius: "0.85rem",
                                        }}>
                                            <p className={styles.muted}>
                                                {texts.no_disputed || "No disputed matches at this time."}
                                            </p>
                                        </div>
                                    ) : (
                                        <ul className={styles.list}>
                                            {matches.map(match => (
                                                <DisputedMatchRow
                                                    key={match.id}
                                                    match={match}
                                                    isSelected={selectedId === match.id}
                                                    onSelect={() => {
                                                        setSelectedId(match.id);
                                                        setAdjMessage(null);
                                                        setAdjScore({ team1: "", team2: "" });
                                                    }}
                                                    texts={texts}
                                                />
                                            ))}
                                        </ul>
                                    )}
                                </div>
                            </article>

                        </div>
                    )}

                </div>
            </div>
        </section>
    );
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

/**
 * Row in the right-hand disputed matches list.
 */
function DisputedMatchRow({ match, isSelected, onSelect, texts }) {
    const subs   = match.scoreSubmissions || [];
    const byRole = Object.fromEntries(subs.map(s => [s.submittedByRole, s]));
    const sub1   = byRole["team1_side"];
    const sub2   = byRole["team2_side"];

    const diffLabel = (sub1 && sub2)
        ? `${sub1.scoreTeam1}-${sub1.scoreTeam2} vs ${sub2.scoreTeam1}-${sub2.scoreTeam2}`
        : null;

    return (
        <li
            className={styles.listItem}
            style={{
                flexDirection: "column",
                alignItems: "flex-start",
                cursor: "pointer",
                padding: "0.75rem",
                borderLeft: isSelected ? "3px solid #f87171" : "3px solid transparent",
                background: isSelected ? "rgba(239,68,68,0.07)" : undefined,
                transition: "background 0.15s, border-color 0.15s",
            }}
            onClick={onSelect}
        >
            <p className={styles.primaryText} style={{ fontSize: "0.9rem" }}>
                {match.team1Name || `Team ${match.team1Id}`}
                <span style={{ color: "var(--text-secondary)", margin: "0 0.4rem", fontWeight: 400 }}>vs</span>
                {match.team2Name || `Team ${match.team2Id}`}
            </p>

            <div style={{ display: "flex", gap: "0.45rem", flexWrap: "wrap", marginTop: "0.3rem" }}>
                {diffLabel && (
                    <span style={{
                        fontSize: "0.76rem",
                        fontWeight: 700,
                        padding: "0.18rem 0.48rem",
                        borderRadius: "999px",
                        border: "1px solid rgba(239,68,68,0.42)",
                        color: "#fca5a5",
                        background: "rgba(127,29,29,0.25)",
                    }}>
                        {diffLabel}
                    </span>
                )}
                {match.ladderName && (
                    <span style={{
                        fontSize: "0.76rem",
                        fontWeight: 600,
                        padding: "0.18rem 0.48rem",
                        borderRadius: "999px",
                        border: "1px solid rgba(14,165,233,0.35)",
                        color: "#bae6fd",
                        background: "rgba(14,116,144,0.15)",
                    }}>
                        {match.ladderName}
                    </span>
                )}
            </div>
        </li>
    );
}

/**
 * Placeholder shown in the left panel when nothing is selected yet.
 */
function EmptyDetailPanel({ texts, hasMatches }) {
    return (
        <div style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            minHeight: "14rem",
            gap: "0.75rem",
            textAlign: "center",
        }}>
            <svg
                xmlns="http://www.w3.org/2000/svg"
                width="36" height="36"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                style={{ color: "var(--text-secondary)", opacity: 0.5 }}
                aria-hidden="true"
            >
                <circle cx="11" cy="11" r="8" />
                <line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
            <p className={styles.muted} style={{ fontSize: "0.9rem", maxWidth: "16rem" }}>
                {hasMatches
                    ? (texts.select_match_prompt || "Select a disputed match from the list to review and adjudicate it.")
                    : (texts.no_disputed || "No disputed matches at this time.")}
            </p>
        </div>
    );
}

/**
 * Left panel content when a match is selected — shows full diff detail
 * plus the adjudication score form.
 */
function AdjudicationPanel({ match, adjScore, setAdjScore, adjSubmitting, adjMessage, onSubmit, onClear, texts }) {
    const subs   = match.scoreSubmissions || [];
    const byRole = Object.fromEntries(subs.map(s => [s.submittedByRole, s]));
    const sub1   = byRole["team1_side"];
    const sub2   = byRole["team2_side"];

    const snapshotRules = Array.isArray(match.ruleSnapshot)
        ? match.ruleSnapshot
        : (match.ruleSnapshot?.rules ?? []);

    return (
        <div style={{ display: "grid", gap: "1.1rem" }}>

            {/* Header */}
            <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "0.5rem" }}>
                <div>
                    <h3 className={styles.panelTitle} style={{ fontSize: "1rem" }}>
                        {match.team1Name || `Team ${match.team1Id}`}
                        <span style={{ color: "var(--text-secondary)", margin: "0 0.4rem", fontWeight: 400 }}>vs</span>
                        {match.team2Name || `Team ${match.team2Id}`}
                    </h3>
                    <p className={styles.muted} style={{ fontSize: "0.78rem", marginTop: "0.2rem" }}>
                        Match #{match.id}
                        {match.weekStartDate ? ` \u00b7 Week of ${match.weekStartDate}` : ""}
                    </p>
                </div>
                <button
                    type="button"
                    onClick={onClear}
                    style={{
                        background: "none",
                        border: "none",
                        cursor: "pointer",
                        color: "var(--text-secondary)",
                        fontSize: "1.1rem",
                        lineHeight: 1,
                        padding: "0.1rem 0.3rem",
                        flexShrink: 0,
                    }}
                    title="Close"
                >
                    &times;
                </button>
            </div>

            {/* Ladder + ruleset */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.6rem" }}>
                <InfoCell
                    label={texts.ladder_label || "Ladder"}
                    value={match.ladderName || (texts.no_ladder || "No ladder")}
                />
                <InfoCell
                    label={texts.ruleset_label || "Rule set"}
                    value={match.ruleSetName || (texts.no_ruleset || "None")}
                />
            </div>

            {/* Submitted scores comparison */}
            <section>
                <h4 className={styles.secondaryText} style={{ fontSize: "0.8rem", marginBottom: "0.4rem" }}>
                    {texts.submitted_scores || "Submitted scores"}
                </h4>
                <div style={{ display: "grid", gap: "0.35rem" }}>
                    {[sub1, sub2].filter(Boolean).map(s => (
                        <SubmissionRow
                            key={s.id}
                            submission={s}
                            team1Name={match.team1Name}
                            team2Name={match.team2Name}
                            texts={texts}
                        />
                    ))}
                </div>
            </section>

            {/* Rules snapshot */}
            {snapshotRules.length > 0 && (
                <section>
                    <h4 className={styles.secondaryText} style={{ fontSize: "0.8rem", marginBottom: "0.4rem" }}>
                        {texts.rules_snapshot_title || "Rules in effect"}
                    </h4>
                    <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "grid", gap: "0.3rem" }}>
                        {snapshotRules.map((rule, i) => (
                            <li
                                key={rule.id ?? i}
                                style={{
                                    padding: "0.38rem 0.6rem",
                                    borderRadius: "0.45rem",
                                    border: "1px solid var(--muted-border)",
                                    background: "rgba(255,255,255,0.025)",
                                }}
                            >
                                <p className={styles.primaryText} style={{ fontSize: "0.82rem" }}>{rule.name}</p>
                                {rule.description && (
                                    <p className={styles.secondaryText} style={{ fontSize: "0.76rem" }}>{rule.description}</p>
                                )}
                            </li>
                        ))}
                    </ul>
                </section>
            )}

            {/* Adjudication form */}
            <section style={{
                borderTop: "1px solid var(--muted-border)",
                paddingTop: "0.9rem",
                display: "grid",
                gap: "0.65rem",
            }}>
                <h4 className={styles.secondaryText} style={{ fontSize: "0.8rem" }}>
                    {texts.adjudicate_title || "Submit decisive score"}
                </h4>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.5rem" }}>
                    <label className={styles.formLabel}>
                        <span style={{ fontSize: "0.78rem" }}>{match.team1Name || "Team 1"}</span>
                        <input
                            className={styles.formInput}
                            type="number"
                            min="0"
                            placeholder="0"
                            value={adjScore.team1}
                            onChange={e => setAdjScore(prev => ({ ...prev, team1: e.target.value }))}
                        />
                    </label>
                    <label className={styles.formLabel}>
                        <span style={{ fontSize: "0.78rem" }}>{match.team2Name || "Team 2"}</span>
                        <input
                            className={styles.formInput}
                            type="number"
                            min="0"
                            placeholder="0"
                            value={adjScore.team2}
                            onChange={e => setAdjScore(prev => ({ ...prev, team2: e.target.value }))}
                        />
                    </label>
                </div>

                <button
                    type="button"
                    className={styles.submitButton}
                    disabled={adjSubmitting}
                    onClick={() => onSubmit(match.id)}
                    style={{ width: "fit-content" }}
                >
                    {adjSubmitting
                        ? (texts.submitting || "Submitting...")
                        : (texts.submit_decisive_score || "Submit decisive score")}
                </button>

                {adjMessage && (
                    <p className={`${styles.notice} ${
                        adjMessage.type === "success" ? styles.noticeSuccess : styles.noticeError
                    }`}>
                        {adjMessage.text}
                    </p>
                )}
            </section>
        </div>
    );
}

/**
 * Single score submission row inside the detail panel.
 */
function SubmissionRow({ submission, team1Name, team2Name, texts }) {
    const labelMap = {
        team1_side:   team1Name || "Team 1",
        team2_side:   team2Name || "Team 2",
        ladder_admin: texts.ladder_admin_label || "Ladder admin",
    };
    const label = labelMap[submission.submittedByRole] ?? submission.submittedByRole;

    return (
        <div style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            padding: "0.45rem 0.65rem",
            borderRadius: "0.5rem",
            border: "1px solid var(--muted-border)",
            background: "rgba(255,255,255,0.03)",
            gap: "0.75rem",
        }}>
            <span className={styles.secondaryText} style={{ fontSize: "0.8rem", minWidth: "6rem" }}>
                {label}
            </span>
            <span className={styles.primaryText} style={{ fontSize: "0.95rem", fontVariantNumeric: "tabular-nums" }}>
                {submission.scoreTeam1} &ndash; {submission.scoreTeam2}
            </span>
            <span className={styles.secondaryText} style={{ fontSize: "0.74rem", whiteSpace: "nowrap" }}>
                {submission.submittedAt
                    ? new Date(submission.submittedAt).toLocaleString()
                    : ""}
            </span>
        </div>
    );
}

/**
 * Small label + value cell used in the info grid.
 */
function InfoCell({ label, value }) {
    return (
        <div>
            <p style={{
                margin: 0,
                fontSize: "0.76rem",
                fontWeight: 600,
                color: "var(--text-secondary)",
                textTransform: "uppercase",
                letterSpacing: "0.06em",
                marginBottom: "0.2rem",
            }}>
                {label}
            </p>
            <p style={{ margin: 0, fontSize: "0.88rem", color: "var(--text-primary)", fontWeight: 600 }}>
                {value}
            </p>
        </div>
    );
}

/**
 * Forbidden notice — shown when the API returns 401/403.
 */
function ForbiddenNotice({ texts, onBack }) {
    return (
        <div className={`${styles.contentGrid} ${styles.contentFade}`}>
            <article className={styles.panel} style={{ gridColumn: "1 / -1" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "0.55rem", marginBottom: "0.5rem" }}>
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
                        {texts.tab_disputed || "Disputed matches"}
                    </h3>
                </div>
                <p className={styles.muted}>
                    {texts.disputed_forbidden
                        || "You do not have permission to view or adjudicate disputed matches. Only club owners and administrators can access this section."}
                </p>
                <button
                    type="button"
                    className={styles.submitButton}
                    onClick={onBack}
                    style={{ marginTop: "0.75rem", width: "fit-content" }}
                >
                    {texts.back || "Back to settings"}
                </button>
            </article>
        </div>
    );
}
