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
    const {
        proposals,
        loading,
        error,
        submitting,
        load,
        setProposalStatus,
    } = useMatchProposals();

    // Only the teams the account actively manages — passed to CreateMatchButton
    const {
        teams: managedTeams,
        loading: managedLoading,
    } = useTeams({ endpoint: "/api/teams/my" });

    function handleMatchCreated() {
        // Optionally navigate to the matches tab or show a toast here.
        // For now a no-op; the panel's own success state is enough feedback.
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
                    {texts.refresh || "Refresh"}
                </button>

                {/* Propose a new match (shown only when account manages at least one team) */}
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
