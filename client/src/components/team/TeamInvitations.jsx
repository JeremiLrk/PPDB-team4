import { useState } from "react";
import { useNavigate } from "react-router-dom";
import commonStyles from "@/style/common/Common.module.css";
import panelStyles from "@/style/common/Panel.module.css";
import buttonStyles from "@/style/common/Buttons.module.css";
import formStyles from "@/style/common/Forms.module.css";
import { usePageTexts } from "@/hooks/common/usePageTexts.js";
import { useLangContext } from "@/context/useLangContext.jsx";
import { useTeamInvitations } from "@/hooks/teams/useTeamInvitations.js";

export default function TeamInvitations() {
    const navigate = useNavigate();
    const { lang } = useLangContext();
    const texts = usePageTexts("teams", lang);
    const { invitations, loading, error, acceptInvitation, rejectInvitation } = useTeamInvitations();
    const [processing, setProcessing] = useState(null);

    async function handleAccept(id, teamId) {
        setProcessing(id);
        await acceptInvitation(id, teamId);
        setProcessing(null);
    }

    async function handleReject(id, teamId) {
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
                            <p className={commonStyles.primaryText}>{inv.team_name}</p>
                            {inv.club_name && (
                                <p className={commonStyles.secondaryText}>{inv.club_name}</p>
                            )}
                            {inv.sport_name && (
                                <p className={commonStyles.secondaryText}>{inv.sport_name}</p>
                            )}
                        </div>

                        <div style={{ display: "flex", gap: "0.6rem", alignItems: "center", flexShrink: 0 }}>
                            <button
                                className={buttonStyles.primaryButton}
                                onClick={() => navigate(`/teams/${inv.team_id}`)}
                                disabled={processing}
                            >
                                View
                            </button>
                            <button
                                className={buttonStyles.primaryButton}
                                onClick={() => handleAccept(inv.id, inv.team_id)}
                                disabled={processing === inv.id}
                            >
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
