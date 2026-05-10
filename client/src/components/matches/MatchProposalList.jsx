import commonStyles from "@/style/common/Common.module.css";
import styles from "@/style/matches/MatchProposalCard.module.css";
import MatchProposalCard from "@/components/matches/MatchProposalCard.jsx";

export default function MatchProposalList({
    proposals,
    loading,
    submitting,
    onStatusChange,
    texts = {},
    statusTexts = {},
    emptyText,
}) {
    if (loading) {
        return <p className={commonStyles.muted}>{texts.loading || "Match proposals loading..."}</p>;
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
                    texts={texts}
                    statusTexts={statusTexts}
                />
            ))}
        </ul>
    );
}
