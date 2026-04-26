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
            {error ? (
                <div style={{ display: "grid", gap: "0.7rem" }}>
                    <p className={commonStyles.muted}>{error}</p>
                    <button className={buttonStyles.primaryButton} type="button" onClick={onReload}>
                        {texts.retry || "Retry"}
                    </button>
                </div>
            ) : null}

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
