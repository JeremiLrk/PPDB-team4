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
    texts = {},
    statusTexts = {},
    emptyText,
}) {
    if (loading) {
        return <p className={commonStyles.muted}>{texts.loading || "Match proposals loading..."}</p>;
    }

    if (error) {
        return (
            <div style={{ display: "grid", gap: "0.7rem" }}>
                <p className={commonStyles.muted}>{error}</p>
                <button className={buttonStyles.primaryButton} type="button" onClick={onReload}>
                    {texts.retry || "Retry"}
                </button>
            </div>
        );
    }

    if (proposals.length === 0) {
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
                    texts={texts}
                    statusTexts={statusTexts}
                />
            ))}
        </ul>
    );
}
