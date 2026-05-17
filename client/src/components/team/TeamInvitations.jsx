// Team management UI component for TeamInvitations.

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import commonStyles from "@/style/common/Common.module.css";
import panelStyles from "@/style/common/Panel.module.css";
import buttonStyles from "@/style/common/Buttons.module.css";
import formStyles from "@/style/common/Forms.module.css";
import dashboardStyles from "@/style/dashboard/Dashboard.module.css";
import { useThemeContext } from "@/context/useThemeContext.jsx";
import { usePageTexts } from "@/hooks/common/usePageTexts.js";
import { useLangContext } from "@/context/useLangContext.jsx";
import { useTeamInvitations } from "@/hooks/teams/useTeamInvitations.js";

export default function TeamInvitations() {
    const navigate = useNavigate();
    const { theme } = useThemeContext();
    const isLight = theme === "light";
    const { lang } = useLangContext();
    const texts = usePageTexts("teams", lang);
    const { invitations, loading, error, acceptInvitation, rejectInvitation } = useTeamInvitations();
    // Local state keeps track of which invitation is currently being processed.
    const [processing, setProcessing] = useState(null);

    async function handleAccept(id, teamId) {
        /*
         Accepts one invitation and keeps the row busy until completion.
        */
        setProcessing(id);
        await acceptInvitation(id, teamId);
        setProcessing(null);
    }

    async function handleReject(id, teamId) {
        /*
         Rejects one invitation using the same processing state.
        */
        setProcessing(id);
        await rejectInvitation(id, teamId);
        setProcessing(null);
    }

    if (loading) {
        return <div className={commonStyles.loading}>Loading invitations...</div>;
    }

    if (invitations.length === 0) {
        return null;
    }

    return (
        <article className={panelStyles.panel}>
            <div className={panelStyles.panelTopRow}>
                <h3 className={panelStyles.panelTitle}>Team Invitations</h3>
                <span className={panelStyles.panelCounter}>{invitations.length}</span>
            </div>

            {error && <p className={commonStyles.warning}>{error}</p>}

            <ul className={panelStyles.list}>
                        {invitations.map(inv => (
                            <li key={inv.id} className={panelStyles.listItem}>
                                <div>
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
                                disabled={processing}
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
