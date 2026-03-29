import { useRef, useEffect } from "react";
import { useRenameTeam }from "@/hooks/useRenameTeam.js";
import { Spinner } from "@/components/forms/Spinner.jsx";
import { SuccessIcon } from "@/components/icon/SuccessIcon.jsx";
import { Field } from "@/components/forms/Field.jsx";
import styles from "@/style/common/Forms.module.css";
import teamStyles from "@/style/TeamSettings.module.css";

/**
 * RenameTeamButton - pencil icon next to the team name that opens a rename panel.
 *
 * Props:
 *   teamId      {number|string}
 *   currentName {string}
 *   onRenamed   {(team: object) => void}
 */
export default function RenameTeamButton({ teamId, currentName, onRenamed }) {
    const {
        isOpen, openPanel, closePanel,
        newName, setNewName,
        loading, error, success,
        submit,
    } = useRenameTeam({ teamId, currentName, onRenamed });

    const panelRef    = useRef(null);
    const triggerRef  = useRef(null);
    const inputRef    = useRef(null);

    // Close on outside click
    useEffect(() => {
        if (!isOpen) return;
        function onOutside(e) {
            if (
                panelRef.current   && !panelRef.current.contains(e.target) &&
                triggerRef.current && !triggerRef.current.contains(e.target)
            ) closePanel();
        }
        document.addEventListener("mousedown", onOutside);
        return () => document.removeEventListener("mousedown", onOutside);
    }, [isOpen, closePanel]);

    // Close on Escape
    useEffect(() => {
        if (!isOpen) return;
        function onKey(e) { if (e.key === "Escape") closePanel(); }
        document.addEventListener("keydown", onKey);
        return () => document.removeEventListener("keydown", onKey);
    }, [isOpen, closePanel]);

    // Auto-focus input
    useEffect(() => {
        if (isOpen) setTimeout(() => inputRef.current?.focus(), 60);
    }, [isOpen]);

    return (
        <div className={styles.wrapper}>
            {/* Trigger - pencil icon button */}
            <button
                ref={triggerRef}
                onClick={isOpen ? closePanel : openPanel}
                className={`${teamStyles.renameBtn} ${isOpen ? teamStyles.renameBtnOpen : ""}`}
                aria-expanded={isOpen}
                aria-haspopup="dialog"
                aria-label="Rename team"
                title="Rename team"
            >
                <PencilIcon />
            </button>

            {/* Panel */}
            <div
                ref={panelRef}
                role="dialog"
                aria-label="Rename team"
                aria-modal="true"
                className={`${styles.panel} ${teamStyles.renamePanel} ${isOpen ? styles.panelOpen : ""}`}
            >
                {/* Header */}
                <div className={styles.panelHeader}>
                    <p className={styles.panelTitle}>Rename Team</p>
                    <button
                        className={styles.closeBtn}
                        onClick={closePanel}
                        aria-label="Close"
                    >
                        ×
                    </button>
                </div>

                {/* Body */}
                <div className={styles.panelBody}>
                    {success ? (
                        <div className={styles.successBody}>
                            <SuccessIcon />
                            <p className={styles.successLabel}>Team renamed!</p>
                        </div>
                    ) : (
                        <>
                            <Field label="New Name">
                                <input
                                    ref={inputRef}
                                    className={styles.formInput}
                                    type="text"
                                    placeholder={currentName}
                                    value={newName}
                                    onChange={e => setNewName(e.target.value)}
                                    onKeyDown={e => e.key === "Enter" && submit()}
                                    disabled={loading}
                                />
                            </Field>

                            {error && <p className={styles.error}>{error}</p>}

                            <div className={teamStyles.confirmActions}>
                                <button
                                    className={teamStyles.cancelBtn}
                                    onClick={closePanel}
                                    disabled={loading}
                                >
                                    Cancel
                                </button>
                                <button
                                    className={styles.submitBtn}
                                    onClick={submit}
                                    disabled={loading || (!newName.trim())}
                                >
                                    {loading ? <><Spinner /> Saving…</> : "Rename"}
                                </button>
                            </div>
                        </>
                    )}
                </div>
            </div>
        </div>
    );
}

function PencilIcon() {
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
            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
        </svg>
    );
}
