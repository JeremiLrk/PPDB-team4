import commonStyles from "@/style/common/Common.module.css";
import styles from "@/style/matches/MatchProposalCard.module.css";
import ItemCard from "@/components/common/ItemCard.jsx";

function parseDate(value) {
    if (!value) return null;
    const parsed = new Date(value);
    return Number.isNaN(parsed.getTime()) ? null : parsed;
}

function formatDateTime(value) {
    const parsed = parseDate(value);
    if (!parsed) return value || "-";

    return parsed.toLocaleString([], {
        dateStyle: "medium",
        timeStyle: "short",
    });
}

function statusClass(status) {
    const normalized = (status || "pending").toLowerCase();
    if (normalized === "accepted" || normalized === "approved") {
        return commonStyles.statusApproved;
    }
    if (normalized === "rejected") {
        return commonStyles.statusRejected;
    }
    if (normalized === "cancelled" || normalized === "canceled") {
        return commonStyles.statusCancelled;
    }
    return commonStyles.statusPending;
}

export default function MatchProposalCard({ proposal, disabled, onStatusChange }) {
    const normalizedStatus = (proposal.status || "pending").toLowerCase();
    const canRespond = normalizedStatus === "pending";
    const canResetToPending = normalizedStatus !== "pending";

    return (
        <ItemCard>
            <div>
                <p className={commonStyles.primaryText}>
                    {proposal.team1Name} vs {proposal.team2Name}
                </p>
                <p className={commonStyles.secondaryText}>
                    {formatDateTime(proposal.proposedStartAt)} - {formatDateTime(proposal.proposedEndAt)}
                </p>
                {proposal.location ? (
                    <p className={commonStyles.secondaryText}>{proposal.location}</p>
                ) : null}
            </div>

            <div
                className={styles.actionRow}
            >
                <span className={`${commonStyles.statusPill} ${statusClass(proposal.status)}`}>
                    {proposal.status}
                </span>

                {canRespond ? (
                    <>
                        <button
                            className={styles.acceptButton}
                            type="button"
                            disabled={disabled}
                            onClick={() => onStatusChange(proposal.id, "accepted")}
                        >
                            Accept
                        </button>
                        <button
                            className={styles.rejectButton}
                            type="button"
                            disabled={disabled}
                            onClick={() => onStatusChange(proposal.id, "rejected")}
                        >
                            Reject
                        </button>
                        <button
                            className={styles.cancelButton}
                            type="button"
                            disabled={disabled}
                            onClick={() => onStatusChange(proposal.id, "cancelled")}
                        >
                            Cancel
                        </button>
                    </>
                ) : null}

                {canResetToPending ? (
                    <button
                        className={styles.resetButton}
                        type="button"
                        disabled={disabled}
                        onClick={() => onStatusChange(proposal.id, "pending")}
                    >
                        Set Pending
                    </button>
                ) : null}
            </div>
        </ItemCard>
    );
}
