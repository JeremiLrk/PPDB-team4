// Team management UI component for TeamInvitations.

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import commonStyles from "@/style/common/Common.module.css";
import panelStyles from "@/style/common/Panel.module.css";
import buttonStyles from "@/style/common/Buttons.module.css";
import formStyles from "@/style/common/Forms.module.css";
import dashboardStyles from "@/style/dashboard/Dashboard.module.css";
import { useLangContext } from "@/context/useLangContext.jsx";
import { useThemeContext } from "@/context/useThemeContext.jsx";
import { usePageTexts } from "@/hooks/common/usePageTexts.js";
import { useTeamInvitations } from "@/hooks/teams/useTeamInvitations.js";

export default function TeamInvitations({ onResolved } = {}) {
    const navigate = useNavigate();
    const { lang } = useLangContext();
    const { theme } = useThemeContext();
    const isLight = theme === "light";
    const dashboardTexts = usePageTexts("dashboard", lang);
    const {
        invitations,
        clubInvitations,
        loading,
        error,
        acceptInvitation,
        rejectInvitation,
        acceptClubInvitation,
        rejectClubInvitation,
    } = useTeamInvitations();
    const teamInvitationRows = Array.isArray(invitations) ? invitations : [];
    const clubInvitationRows = Array.isArray(clubInvitations) ? clubInvitations : [];
    // Local state keeps track of which invitation is currently being processed.
    const [processing, setProcessing] = useState(null);
    const inviteTagStyle = {
        display: "inline-flex",
        alignItems: "center",
        width: "fit-content",
        padding: "0.15rem 0.5rem",
        borderRadius: "999px",
        border: isLight ? "1px solid rgba(14, 165, 233, 0.35)" : "1px solid rgba(56, 189, 248, 0.35)",
        background: isLight ? "rgba(14, 165, 233, 0.08)" : "rgba(15, 118, 110, 0.24)",
        color: isLight ? "#0369a1" : "#7dd3fc",
        fontSize: "0.72rem",
        fontWeight: 700,
        letterSpacing: "0.04em",
        textTransform: "uppercase",
        marginBottom: "0.45rem",
    };

    async function handleAccept(id, teamId) {
        /*
         Accepts one invitation and keeps the row busy until completion.
        */
        setProcessing(id);
        try {
            await acceptInvitation(id, teamId);
            try {
                await onResolved?.();
            } catch {
                // Refresh failures should not undo a successful invite response.
            }
        } finally {
            setProcessing(null);
        }
    }

    async function handleReject(id, teamId) {
        /*
         Rejects one invitation using the same processing state.
        */
        setProcessing(id);
        try {
            await rejectInvitation(id, teamId);
            try {
                await onResolved?.();
            } catch {
                // Refresh failures should not undo a successful invite response.
            }
        } finally {
            setProcessing(null);
        }
    }

    async function handleClubAccept(id, teamId) {
        /*
         Accepts one club invitation for a managed team.
        */
        setProcessing(`club-${id}`);
        try {
            await acceptClubInvitation(id, teamId);
            try {
                await onResolved?.();
            } catch {
                // Refresh failures should not undo a successful invite response.
            }
        } finally {
            setProcessing(null);
        }
    }

    async function handleClubReject(id, teamId) {
        /*
         Rejects one club invitation for a managed team.
        */
        setProcessing(`club-${id}`);
        try {
            await rejectClubInvitation(id, teamId);
            try {
                await onResolved?.();
            } catch {
                // Refresh failures should not undo a successful invite response.
            }
        } finally {
            setProcessing(null);
        }
    }

    if (loading) {
        return <div className={commonStyles.loading}>Loading invitations...</div>;
    }

    if (teamInvitationRows.length === 0 && clubInvitationRows.length === 0) {
        return null;
    }

    return (
        <article className={panelStyles.panel}>
            <div className={panelStyles.panelTopRow}>
                <h3 className={panelStyles.panelTitle}>Team Invitations</h3>
                <span className={panelStyles.panelCounter}>{teamInvitationRows.length + clubInvitationRows.length}</span>
            </div>

            {error && <p className={commonStyles.warning}>{error}</p>}

            <ul className={panelStyles.list}>
                {clubInvitationRows.map((inv) => (
                    <li key={`club-${inv.id}`} className={panelStyles.listItem}>
                        <div>
                            <p style={inviteTagStyle}>
                                {dashboardTexts.ladder_invite || "Ladder invite"}
                            </p>
                            <p
                                className={dashboardStyles.teamCardName}
                                style={{
                                    color: isLight ? "#020617" : "#ffffff",
                                    WebkitTextFillColor: isLight ? "#020617" : "#ffffff",
                                }}
                            >
                                {inv.teamName || inv.team_name}
                            </p>
                            <p
                                className={dashboardStyles.teamCardMeta}
                                style={{
                                    color: isLight ? "#334155" : "#cbd5e1",
                                    WebkitTextFillColor: isLight ? "#334155" : "#cbd5e1",
                                    }}
                                >
                                {(inv.clubName || inv.club_name) ? `${dashboardTexts.club_invite || "Club invite"}: ${inv.clubName || inv.club_name}` : (dashboardTexts.club_invite || "Club invite")}
                            </p>
                            {(inv.ladderName || inv.ladder_name) && (
                                <p
                                    className={dashboardStyles.teamCardMeta}
                                    style={{
                                        color: isLight ? "#334155" : "#cbd5e1",
                                        WebkitTextFillColor: isLight ? "#334155" : "#cbd5e1",
                                    }}
                                >
                                    Ladder: {inv.ladderName || inv.ladder_name}
                                </p>
                            )}
                            {(inv.sportName || inv.sport_name) && (
                                <p
                                    className={dashboardStyles.teamCardMeta}
                                    style={{
                                        color: isLight ? "#334155" : "#cbd5e1",
                                        WebkitTextFillColor: isLight ? "#334155" : "#cbd5e1",
                                    }}
                                >
                                    Sport: {inv.sportName || inv.sport_name}
                                </p>
                            )}
                            {(inv.sportMismatch || inv.sport_mismatch) && (inv.ladderSportName || inv.ladder_sport_name) && (inv.sportName || inv.sport_name) ? (
                                <p
                                    className={dashboardStyles.teamCardMeta}
                                    style={{
                                        color: isLight ? "#b45309" : "#fbbf24",
                                        WebkitTextFillColor: isLight ? "#b45309" : "#fbbf24",
                                    }}
                                >
                                    Accepting this invite will change the team's sport to {inv.ladderSportName || inv.ladder_sport_name}.
                                </p>
                            ) : null}
                        </div>

                        <div style={{ display: "flex", gap: "0.6rem", alignItems: "center", flexShrink: 0 }}>
                            <button
                                className={buttonStyles.primaryButton}
                                onClick={() => navigate(`/teams/${inv.teamId || inv.team_id}`)}
                                disabled={processing === `club-${inv.id}`}
                            >
                                View
                            </button>
                            <button
                                className={buttonStyles.primaryButton}
                                onClick={() => handleClubAccept(inv.id, inv.teamId || inv.team_id)}
                                disabled={processing === `club-${inv.id}`}
                            >
                                {processing === `club-${inv.id}` ? "..." : "Accept"}
                            </button>
                            <button
                                className={`${buttonStyles.primaryButton} ${formStyles.danger}`}
                                onClick={() => handleClubReject(inv.id, inv.teamId || inv.team_id)}
                                disabled={processing === `club-${inv.id}`}
                            >
                                {processing === `club-${inv.id}` ? "..." : "Reject"}
                            </button>
                        </div>
                    </li>
                ))}
                {teamInvitationRows.map((inv) => (
                    <li key={inv.id} className={panelStyles.listItem}>
                        <div>
                            <p style={inviteTagStyle}>
                                {dashboardTexts.player_invite || "Player invite"}
                            </p>
                            {/* Team name, club, and sport are stacked so the invite stays readable on small screens. */}
                            <p
                                className={dashboardStyles.teamCardName}
                                style={{
                                    color: isLight ? "#020617" : "#ffffff",
                                    WebkitTextFillColor: isLight ? "#020617" : "#ffffff",
                                }}
                            >
                                {inv.team_name}
                            </p>
                            {inv.club_name && (
                                <p
                                    className={dashboardStyles.teamCardMeta}
                                    style={{
                                        color: isLight ? "#334155" : "#cbd5e1",
                                        WebkitTextFillColor: isLight ? "#334155" : "#cbd5e1",
                                    }}
                                >
                                    {inv.club_name}
                                </p>
                            )}
                            {inv.sport_name && (
                                <p
                                    className={dashboardStyles.teamCardMeta}
                                    style={{
                                        color: isLight ? "#334155" : "#cbd5e1",
                                        WebkitTextFillColor: isLight ? "#334155" : "#cbd5e1",
                                    }}
                                >
                                    {inv.sport_name}
                                </p>
                            )}
                        </div>

                        <div style={{ display: "flex", gap: "0.6rem", alignItems: "center", flexShrink: 0 }}>
                            <button
                                className={buttonStyles.primaryButton}
                                onClick={() => navigate(`/teams/${inv.team_id}`)}
                                disabled={processing === inv.id}
                            >
                                {/* View opens the team page without changing invite state. */}
                                View
                            </button>
                            <button
                                className={buttonStyles.primaryButton}
                                onClick={() => handleAccept(inv.id, inv.team_id)}
                                disabled={processing === inv.id}
                            >
                                {/* Accept and reject are separate API actions so club owners can respond immediately. */}
                                {processing === inv.id ? "..." : "Accept"}
                            </button>
                            <button
                                className={`${buttonStyles.primaryButton} ${formStyles.danger}`}
                                onClick={() => handleReject(inv.id, inv.team_id)}
                                disabled={processing === inv.id}
                            >
                                {processing === inv.id ? "..." : "Reject"}
                            </button>
                        </div>
                    </li>
                ))}
            </ul>
        </article>
    );
}
