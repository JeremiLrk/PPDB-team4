import commonStyles from "@/style/common/Common.module.css";
import styles from "@/style/matches/MatchProposalCard.module.css";
import ItemCard from "@/components/common/ItemCard.jsx";
import { statusLabel } from "@/components/dashboard/dashboardUtils.js";

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

export default function MatchProposalCard({ proposal, disabled, onStatusChange, texts = {}, statusTexts = {} }) {
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
                    {statusLabel(proposal.status, statusTexts)}
                </span>

                {canRespond ? (
                    <>
                        <button
                            className={styles.acceptButton}
                            type="button"
                            disabled={disabled}
                            onClick={() => onStatusChange(proposal.id, "accepted")}
                        >
                            {texts.accept || "Accept"}
                        </button>
                        <button
                            className={styles.rejectButton}
                            type="button"
                            disabled={disabled}
                            onClick={() => onStatusChange(proposal.id, "rejected")}
                        >
                            {texts.reject || "Reject"}
                        </button>
                        <button
                            className={styles.cancelButton}
                            type="button"
                            disabled={disabled}
                            onClick={() => onStatusChange(proposal.id, "cancelled")}
                        >
                            {texts.cancel || "Cancel"}
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
                        {texts.reset_pending || "Set back to pending"}
                    </button>
                ) : null}
            </div>
        </ItemCard>
    );
}
