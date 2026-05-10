import buttonStyles from "@/style/common/Buttons.module.css";
import commonStyles from "@/style/common/Common.module.css";
import panelStyles from "@/style/common/Panel.module.css";
import MatchProposalCard from "@/components/matches/MatchProposalCard.jsx";

export default function MatchProposalList({
    proposals,
    loading,
    error,
    submitting,
    onReload,
    onStatusChange,
    texts = {},
    statusTexts = {},
}) {
    return (
        <>
            {/* The list stays thin: it only chooses which state to show and
                delegates the actual proposal rendering to the card component. */}
            {error ? (
                <div style={{ display: "grid", gap: "0.7rem" }}>
                    <p className={commonStyles.muted}>{error}</p>
                    <button className={buttonStyles.primaryButton} type="button" onClick={onReload}>
                        {texts.retry || "Retry"}
                    </button>
                </div>
            ) : null}

            {/* Loading, empty, and populated states are mutually exclusive so the
                user never sees stale proposals under a spinner or error message. */}
            {loading ? <p className={commonStyles.muted}>{texts.loading || "Match proposals loading..."}</p> : null}

            {!loading && !error && proposals.length === 0 ? (
                <p className={commonStyles.muted}>{texts.empty || "No match proposals yet."}</p>
            ) : null}

            {!loading && proposals.length > 0 ? (
                <ul className={panelStyles.list}>
                    {proposals.map((proposal) => (
                        <MatchProposalCard
                            key={proposal.id}
                            proposal={proposal}
                            disabled={submitting}
                            onStatusChange={onStatusChange}
                            texts={texts}
                            statusTexts={statusTexts}
                        />
                    ))}
                </ul>
            ) : null}
        </>
    );
}
