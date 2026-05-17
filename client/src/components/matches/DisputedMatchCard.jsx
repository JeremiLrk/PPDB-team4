// Match workflow UI component for DisputedMatchCard.

import { useState } from "react";
import styles from "@/style/ClubSettings.module.css";

/**
 * Shows the full detail of one disputed match:
 *   - Which teams are involved and on which ladder
 *   - What score each side submitted and how they differ
 *   - The rule snapshot (frozen rules that apply to this match)
 *
 * @param {{ match: object, texts: object }} props
 */
function SubmissionRow({ role, submission, team1Name, team2Name, texts }) {
    /*
     Renders one submitted score row with its source role and timestamp.
    */
    const labelMap = {
        team1_side:   team1Name || texts.team1 || "Team 1",
        team2_side:   team2Name || texts.team2 || "Team 2",
        ladder_admin: texts.ladder_admin_label || "Ladder admin",
    };

    const label = labelMap[role] ?? role;

    return (
        <div style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            padding: "0.55rem 0.7rem",
            borderRadius: "0.5rem",
            background: "rgba(255,255,255,0.04)",
            border: "1px solid var(--muted-border)",
            gap: "1rem",
        }}>
            <span className={styles.secondaryText} style={{ fontSize: "0.82rem", minWidth: "7rem" }}>
                {label}
            </span>
            <span className={styles.primaryText} style={{ fontSize: "0.96rem", letterSpacing: "0.04em" }}>
                {submission.scoreTeam1} &ndash; {submission.scoreTeam2}
            </span>
            <span className={styles.secondaryText} style={{ fontSize: "0.78rem" }}>
                {submission.submittedAt
                    ? new Date(submission.submittedAt).toLocaleString()
                    : ""}
            </span>
        </div>
    );
}

function RulesList({ rules, texts }) {
    /*
     Renders the frozen rule snapshot attached to the disputed match.
    */
    if (!rules || rules.length === 0) {
        return (
            <p className={styles.muted} style={{ fontSize: "0.82rem", marginTop: "0.4rem" }}>
                {texts.no_rules_snapshot || "No rules recorded for this match."}
            </p>
        );
    }

    return (
        <ul className={styles.list} style={{ marginTop: "0.5rem", display: "grid", gap: "0.35rem" }}>
            {rules.map((rule, idx) => (
                <li key={rule.id ?? idx} style={{
                    padding: "0.4rem 0.6rem",
                    borderRadius: "0.45rem",
                    border: "1px solid var(--muted-border)",
                    background: "rgba(255,255,255,0.03)",
                }}>
                    <p className={styles.primaryText} style={{ fontSize: "0.84rem" }}>
                        {rule.name}
                    </p>
                    {rule.description && (
                        <p className={styles.secondaryText} style={{ fontSize: "0.78rem" }}>
                            {rule.description}
                        </p>
                    )}
                </li>
            ))}
        </ul>
    );
}

export default function DisputedMatchCard({ match, texts = {} }) {
    /*
     Renders one disputed match with expandable detail content.
    */
    const [expanded, setExpanded] = useState(false);

    /*
     Keeps this card's detail panel local to the row it belongs to.
    */

    /*
     Groups score submissions by role so the summary can compare them.
    */
    const subs = match.scoreSubmissions || [];
    const byRole = Object.fromEntries(subs.map(s => [s.submittedByRole, s]));
    const sub1   = byRole["team1_side"];
    const sub2   = byRole["team2_side"];

    const diffLabel = (sub1 && sub2)
        ? `${sub1.scoreTeam1}-${sub1.scoreTeam2} vs ${sub2.scoreTeam1}-${sub2.scoreTeam2}`
        : null;

    /*
     Prefers the frozen rules snapshot stored on the match.
    */
    const snapshotRules = Array.isArray(match.ruleSnapshot)
        ? match.ruleSnapshot
        : (match.ruleSnapshot?.rules ?? null);

    const ladderName  = match.ladderName  ?? (match.ladder?.name ?? null);
    const ruleSetName = match.ruleSetName ?? (match.ruleset?.name ?? null);

    const formattedDate = match.proposedStartAt
        ? new Date(match.proposedStartAt).toLocaleString()
        : match.weekStartDate ?? null;

    return (
        <li style={{
            borderRadius: "0.85rem",
            border: "1px solid rgba(239, 68, 68, 0.35)",
            background: "rgba(127, 29, 29, 0.12)",
            overflow: "hidden",
            transition: "box-shadow 0.18s ease",
        }}>
            {/* --- Summary row --- */}
            <div style={{
                display: "flex",
                alignItems: "center",
                gap: "0.75rem",
                padding: "0.8rem 1rem",
                flexWrap: "wrap",
            }}>
                {/* Teams */}
                <span className={styles.primaryText} style={{ flex: "1 1 auto", fontSize: "0.95rem" }}>
                    {match.team1Name || `Team ${match.team1Id}`}
                    <span style={{ color: "var(--text-secondary)", margin: "0 0.4rem" }}>vs</span>
                    {match.team2Name || `Team ${match.team2Id}`}
                </span>

                {/* Score conflict badge */}
                {diffLabel && (
                    <span style={{
                        fontSize: "0.78rem",
                        fontWeight: 700,
                        padding: "0.22rem 0.55rem",
                        borderRadius: "999px",
                        border: "1px solid rgba(239,68,68,0.45)",
                        color: "#fca5a5",
                        background: "rgba(127,29,29,0.3)",
                        whiteSpace: "nowrap",
                    }}>
                        {diffLabel}
                    </span>
                )}

                {/* Ladder badge */}
                {ladderName && (
                    <span style={{
                        fontSize: "0.78rem",
                        fontWeight: 600,
                        padding: "0.22rem 0.55rem",
                        borderRadius: "999px",
                        border: "1px solid rgba(14,165,233,0.38)",
                        color: "#bae6fd",
                        background: "rgba(14,116,144,0.18)",
                        whiteSpace: "nowrap",
                    }}>
                        {ladderName}
                    </span>
                )}

                {/* Date */}
                {formattedDate && (
                    <span className={styles.secondaryText} style={{ fontSize: "0.78rem", whiteSpace: "nowrap" }}>
                        {formattedDate}
                    </span>
                )}

                {/* Expand toggle */}
                <button
                    type="button"
                    onClick={() => setExpanded(prev => !prev)}
                    style={{
                        background: "none",
                        border: "none",
                        cursor: "pointer",
                        color: "var(--text-secondary)",
                        fontSize: "0.82rem",
                        padding: "0.2rem 0.5rem",
                        borderRadius: "0.35rem",
                        transition: "color 0.15s",
                        flexShrink: 0,
                    }}
                >
                    {expanded
                        ? (texts.collapse || "Collapse")
                        : (texts.view_details || "Details")}
                </button>
            </div>

            {/* --- Expanded detail panel --- */}
            {expanded && (
                <div style={{
                    borderTop: "1px solid rgba(239,68,68,0.22)",
                    padding: "0.9rem 1rem",
                    display: "grid",
                    gap: "1.1rem",
                }}>
                    {/* Score submissions */}
                    <section>
                        <h4 className={styles.secondaryText} style={{ fontSize: "0.82rem", marginBottom: "0.45rem" }}>
                            {texts.submitted_scores || "Submitted scores"}
                        </h4>
                        <div style={{ display: "grid", gap: "0.4rem" }}>
                            {subs.length === 0 && (
                                <p className={styles.muted} style={{ fontSize: "0.82rem" }}>
                                    {texts.no_submissions || "No submissions found."}
                                </p>
                            )}
                            {subs.map(s => (
                                <SubmissionRow
                                    key={s.id}
                                    role={s.submittedByRole}
                                    submission={s}
                                    team1Name={match.team1Name}
                                    team2Name={match.team2Name}
                                    texts={texts}
                                />
                            ))}
                        </div>
                    </section>

                    {/* Ladder + ruleset context */}
                    <section style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.8rem" }}>
                        <div>
                            <h4 className={styles.secondaryText} style={{ fontSize: "0.82rem", marginBottom: "0.25rem" }}>
                                {texts.ladder_label || "Ladder"}
                            </h4>
                            <p className={styles.primaryText} style={{ fontSize: "0.9rem" }}>
                                {ladderName || (texts.no_ladder || "No ladder")}
                            </p>
                            {match.ladderId && (
                                <p className={styles.secondaryText} style={{ fontSize: "0.76rem" }}>
                                    ID: {match.ladderId}
                                </p>
                            )}
                        </div>

                        <div>
                            <h4 className={styles.secondaryText} style={{ fontSize: "0.82rem", marginBottom: "0.25rem" }}>
                                {texts.ruleset_label || "Rule set"}
                            </h4>
                            <p className={styles.primaryText} style={{ fontSize: "0.9rem" }}>
                                {ruleSetName || (texts.no_ruleset || "No rule set")}
                            </p>
                        </div>
                    </section>

                    {/* Frozen rule snapshot */}
                    <section>
                        <h4 className={styles.secondaryText} style={{ fontSize: "0.82rem", marginBottom: "0.3rem" }}>
                            {texts.rules_snapshot_title || "Rules in effect at match time"}
                        </h4>
                        <RulesList rules={snapshotRules} texts={texts} />
                    </section>

                    {/* Match ID / sport type meta */}
                    <p className={styles.muted} style={{ fontSize: "0.76rem" }}>
                        {texts.match_id_label || "Match"} #{match.id}
                        {match.sportTypeId ? ` \u00b7 Sport type ID: ${match.sportTypeId}` : ""}
                    </p>
                </div>
            )}
        </li>
    );
}
