// Match workflow UI component for MatchProposalList.

import buttonStyles from "@/style/common/Buttons.module.css";
import commonStyles from "@/style/common/Common.module.css";
import styles from "@/style/matches/MatchProposalCard.module.css";
import MatchProposalCard from "@/components/matches/MatchProposalCard.jsx";

export default function MatchProposalList({
    proposals,
    loading,
    error,
    submitting,
    onReload,
    onStatusChange,
    onReportScore,
    reportingMatchId,
    scoreValues,
    onScoreChange,
    onScoreSubmit,
    onCancelScore,
    scoreSubmitting,
    canUpdateProposal,
    currentUserId,
    texts = {},
    statusTexts = {},
    emptyText,
}) {
    /*
     Renders the match proposals in loading, error, or list state.
    */
    if (loading) {
        // Loading state stays compact so the list can swap in place.
        return <p className={commonStyles.muted}>{texts.loading || "Match proposals loading..."}</p>;
    }

    if (error) {
        /*
         Shows the backend error and a retry button.
        */
        return (
            <div style={{ display: "grid", gap: "0.7rem" }}>
                {/* Surface the backend error and keep the retry action next to it. */}
                <p className={commonStyles.muted}>{error}</p>
                <button className={buttonStyles.primaryButton} type="button" onClick={onReload}>
                    {texts.retry || "Retry"}
                </button>
            </div>
        );
    }

    if (proposals.length === 0) {
        /*
         Shows an explicit empty state when there are no proposals.
        */
        return <p className={commonStyles.muted}>{emptyText || texts.empty || "No match proposals yet."}</p>;
    }

    return (
        <ul className={styles.list}>
            {proposals.map((proposal) => (
                <MatchProposalCard
                    key={proposal.id}
                    proposal={proposal}
                    disabled={submitting}
                    onStatusChange={onStatusChange}
                    onReportScore={onReportScore}
                    reportingMatchId={reportingMatchId}
                    scoreValues={scoreValues}
                    onScoreChange={onScoreChange}
                    onScoreSubmit={onScoreSubmit}
                    onCancelScore={onCancelScore}
                    scoreSubmitting={scoreSubmitting}
                    canUpdate={canUpdateProposal ? canUpdateProposal(proposal) : true}
                    currentUserId={currentUserId}
                    texts={texts}
                    statusTexts={statusTexts}
                />
            ))}
        </ul>
    );
}
