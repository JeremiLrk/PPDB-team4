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
}) {
    return (
        <>
            {error ? (
                <div style={{ display: "grid", gap: "0.7rem" }}>
                    <p className={commonStyles.muted}>{error}</p>
                    <button className={buttonStyles.primaryButton} type="button" onClick={onReload}>
                        Opnieuw proberen
                    </button>
                </div>
            ) : null}

            {loading ? <p className={commonStyles.muted}>Wedstrijdvoorstellen laden...</p> : null}

            {!loading && !error && proposals.length === 0 ? (
                <p className={commonStyles.muted}>Nog geen wedstrijdvoorstellen.</p>
            ) : null}

            {!loading && proposals.length > 0 ? (
                <ul className={panelStyles.list}>
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
