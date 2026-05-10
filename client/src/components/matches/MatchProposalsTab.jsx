import { useState } from "react";
import animationStyles from "@/style/common/Animation.module.css";
import buttonStyles from "@/style/common/Buttons.module.css";
import panelStyles from "@/style/common/Panel.module.css";
import { useMatchProposals } from "@/hooks/useMatchProposals.js";
import MatchProposalList from "@/components/matches/MatchProposalList.jsx";
import { useLangContext } from "@/context/useLangContext.jsx";
import { usePageTexts } from "@/hooks/common/usePageTexts.js";

import { useTeams }     from "@/hooks/teams/useTeams.js";
import CreateMatchButton    from "@/components/matches/CreateMatchButton.jsx";

export default function MatchProposalsTab() {
    const { lang } = useLangContext();
    const texts = usePageTexts("matches", lang);
    const dashboardTexts = usePageTexts("dashboard", lang);
    const [showArchived, setShowArchived] = useState(false);
    const {
        proposals,
        loading,
        error,
        submitting,
        load,
        setProposalStatus,
    } = useMatchProposals({ archived: showArchived });

    // Only the teams the account actively manages are eligible for match creation.
    // The button uses this list to build the proposal wizard.
    const {
        teams: managedTeams,
        loading: managedLoading,
    } = useTeams({ endpoint: "/api/teams/my" });

    function handleMatchCreated() {
        void load();
    }

    return (
        <article
            className={`${panelStyles.panel} ${animationStyles.contentFade}`}
            style={{ display: "grid", gap: "1rem" }}
        >
            <div
                style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    flexWrap: "wrap",
                    gap: "0.75rem",
                }}
            >
                <h3 className={panelStyles.panelTitle} style={{ margin: 0 }}>
                    {texts.title || "Weekly Match Proposals"}
                    <span className={panelStyles.panelCounter} style={{ marginLeft: "0.6rem" }}>
                        {proposals.length}
                    </span>
                </h3>

                <button
                    className={buttonStyles.primaryButton}
                    type="button"
                    onClick={load}
                    disabled={loading}
                >
                    {/* Manual refresh always re-reads the proposals from the backend. */}
                    {texts.refresh || "Refresh"}
                </button>

                <button
                    className={buttonStyles.primaryButton}
                    type="button"
                    onClick={() => setShowArchived((current) => !current)}
                    disabled={loading}
                >
                    {/* This is just a filter switch; the hook asks the API again. */}
                    {showArchived
                        ? (texts.show_active || "Show active")
                        : (texts.show_archived || "Show archived")}
                </button>

                {/* Wait for managed teams so the wizard gets the actual eligible list. */}
                {!managedLoading && (
                    <CreateMatchButton
                        managedTeams={managedTeams}
                        onCreated={handleMatchCreated}
                    />
                )}
            </div>

            <MatchProposalList
                proposals={proposals}
                loading={loading}
                error={error}
                submitting={submitting}
                onReload={load}
                onStatusChange={setProposalStatus}
                texts={texts}
                statusTexts={dashboardTexts}
            />
        </article>
    );
}
