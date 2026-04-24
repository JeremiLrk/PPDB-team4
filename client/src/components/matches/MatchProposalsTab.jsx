import animationStyles from "@/style/common/Animation.module.css";
import buttonStyles from "@/style/common/Buttons.module.css";
import panelStyles from "@/style/common/Panel.module.css";
import { useMatchProposals } from "@/hooks/useMatchProposals.js";
import MatchProposalList from "@/components/matches/MatchProposalList.jsx";

export default function MatchProposalsTab() {
    const {
        proposals,
        loading,
        error,
        submitting,
        load,
        setProposalStatus,
    } = useMatchProposals();

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
                    Weekly Match Proposals
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
                    Refresh
                </button>
            </div>

            <MatchProposalList
                proposals={proposals}
                loading={loading}
                error={error}
                submitting={submitting}
                onReload={load}
                onStatusChange={setProposalStatus}
            />
        </article>
    );
}
