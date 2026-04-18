import commonStyles from "@/style/common/Common.module.css";
import MatchProposalCard from "@/components/matches/MatchProposalCard.jsx";

export default function MatchProposalList({
    proposals,
    loading,
    error,
    submitting,
    onReload,
    onStatusChange,
}) {
    return (
        <>
            {error ? (
                <div style={{ display: "grid", gap: "0.7rem" }}>
                    <p className={commonStyles.muted}>{error}</p>
                    <button className={commonStyles.primaryButton} type="button" onClick={onReload}>
                        Retry
                    </button>
                </div>
            ) : null}

            {loading ? <p className={commonStyles.muted}>Loading match proposals...</p> : null}

            {!loading && !error && proposals.length === 0 ? (
                <p className={commonStyles.muted}>No match proposals yet.</p>
            ) : null}

            {!loading && proposals.length > 0 ? (
                <ul className={commonStyles.list}>
                    {proposals.map((proposal) => (
                        <MatchProposalCard
                            key={proposal.id}
                            proposal={proposal}
                            disabled={submitting}
                            onStatusChange={onStatusChange}
                        />
                    ))}
                </ul>
            ) : null}
        </>
    );
}
