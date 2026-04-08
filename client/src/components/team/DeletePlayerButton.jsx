import { useRef, useEffect } from "react";
import { useDeletePlayer }from "@/hooks/teams/useDeletePlayer.js";
import { Spinner } from "@/components/forms/Spinner.jsx";
import styles from "@/style/common/Forms.module.css";
import teamStyles from "@/style/TeamSettings.module.css";

/**
 * DeletePlayerButton - trash icon that opens a confirmation dropdown.
 *
 * Props:
 *   teamId    {number|string}
 *   playerId  {number|string}  - the account/player id to remove
 *   onDeleted {() => void}     - called after successful deletion
 */
export default function DeletePlayerButton({ teamId, playerId, onDeleted }) {
    const {
        isOpen, openDialog, closeDialog,
        confirmDelete, loading, error,
    } = useDeletePlayer({ teamId, playerId, onDeleted });

    const panelRef   = useRef(null);
    const triggerRef = useRef(null);

    // Close on outside click
    useEffect(() => {
        if (!isOpen) return;
        function onOutside(e) {
            if (
                panelRef.current   && !panelRef.current.contains(e.target) &&
                triggerRef.current && !triggerRef.current.contains(e.target)
            ) closeDialog();
        }
        document.addEventListener("mousedown", onOutside);
        return () => document.removeEventListener("mousedown", onOutside);
    }, [isOpen, closeDialog]);

    // Close on Escape
    useEffect(() => {
        if (!isOpen) return;
        function onKey(e) { if (e.key === "Escape") closeDialog(); }
        document.addEventListener("keydown", onKey);
        return () => document.removeEventListener("keydown", onKey);
    }, [isOpen, closeDialog]);

    return (
        <div className={styles.wrapper}>
            {/* Trigger - small trash button */}
            <button
                ref={triggerRef}
                onClick={isOpen ? closeDialog : openDialog}
                className={`${teamStyles.deleteBtn} ${isOpen ? teamStyles.deleteBtnOpen : ""}`}
                aria-expanded={isOpen}
                aria-haspopup="dialog"
                aria-label="Remove player"
                title="Remove player"
            >
                <TrashIcon />
            </button>

            {/* Confirmation panel */}
            <div
                ref={panelRef}
                role="dialog"
                aria-label="Confirm player removal"
                aria-modal="true"
                className={`${styles.panel} ${teamStyles.confirmPanel} ${isOpen ? styles.panelOpen : ""}`}
            >
                {/* Header */}
                <div className={styles.panelHeader}>
                    <p className={styles.panelTitle}>Remove Player</p>
                    <button
                        className={styles.closeBtn}
                        onClick={closeDialog}
                        aria-label="Close"
                    >
                        ×
                    </button>
                </div>

                {/* Body */}
                <div className={styles.panelBody}>
                    <p className={teamStyles.confirmText}>
                        Are you sure you want to remove this player from the team?
                    </p>

                    {error && <p className={styles.error}>{error}</p>}

                    <div className={teamStyles.confirmActions}>
                        <button
                            className={teamStyles.cancelBtn}
                            onClick={closeDialog}
                            disabled={loading}
                        >
                            Cancel
                        </button>
                        <button
                            className={teamStyles.confirmDeleteBtn}
                            onClick={confirmDelete}
                            disabled={loading}
                        >
                            {loading ? <><Spinner /> Removing…</> : "Remove"}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}

function TrashIcon() {
    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.2"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
        >
            <polyline points="3 6 5 6 21 6" />
            <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
            <path d="M10 11v6M14 11v6" />
            <path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2" />
        </svg>
    );
}
