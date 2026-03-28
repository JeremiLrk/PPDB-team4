import { useRef, useEffect } from "react";
import styles from "@/style/Forms.module.css";

import { useCreateTeam } from "@/hooks/useCreateTeam.js";
import { useSportTypes } from "@/hooks/useSportTypes.js";
import {PlusIcon} from "@/components/icon/PlusIcon.jsx";
import {SuccessIcon} from "@/components/icon/SuccessIcon.jsx";
import {Field} from "@/components/forms/Field.jsx";
import {Spinner} from "@/components/forms/Spinner.jsx";

/**
 * @param {{
 *   clubs?:     { id: number, name: string }[],
 *   onCreated?: (team: object) => void,
 * }} props
 */
export default function CreateTeamButton({ clubs = [], onCreated }) {
    const {
        form, step, error,
        openForm, closeForm, updateField, submit,
        isOpen, isLoading, isSuccess,
    } = useCreateTeam({ onCreated });

    const { sportTypes, loading: sportTypesLoading } = useSportTypes();

    const panelRef  = useRef(null);
    const triggerRef = useRef(null);

    // Close on outside click
    useEffect(() => {
        if (!isOpen) return;
        function handleOutside(e) {
            if (
                panelRef.current   && !panelRef.current.contains(e.target) &&
                triggerRef.current && !triggerRef.current.contains(e.target)
            ) {
                closeForm();
            }
        }
        document.addEventListener("mousedown", handleOutside);
        return () => document.removeEventListener("mousedown", handleOutside);
    }, [isOpen, closeForm]);

    // Close on Escape
    useEffect(() => {
        if (!isOpen) return;
        function handleKey(e) {
            if (e.key === "Escape") closeForm();
        }
        document.addEventListener("keydown", handleKey);
        return () => document.removeEventListener("keydown", handleKey);
    }, [isOpen, closeForm]);

    return (
        <div className={styles.wrapper}>
            {/*  Trigger  */}
            <button
                ref={triggerRef}
                onClick={isOpen ? closeForm : openForm}
                className={`${styles.trigger} ${isOpen ? styles.triggerOpen : ""}`}
                aria-expanded={isOpen}
                aria-haspopup="dialog"
            >
                <PlusIcon rotated={isOpen} />
                New Team
            </button>

            {/*  Panel  */}
            <div
                ref={panelRef}
                role="dialog"
                aria-label="Create team"
                aria-modal="true"
                className={`${styles.panel} ${isOpen ? styles.panelOpen : ""}`}
            >
                {/* Header */}
                <div className={styles.panelHeader}>
                    <p className={styles.panelTitle}>Create Team</p>
                    <button
                        className={styles.closeBtn}
                        onClick={closeForm}
                        aria-label="Close"
                    >
                        ×
                    </button>
                </div>

                {/* Body */}
                <div className={styles.panelBody}>
                    {isSuccess ? (
                        <div className={styles.successBody}>
                            <SuccessIcon />
                            <p className={styles.successLabel}>Team created!</p>
                        </div>
                    ) : (
                        <>
                            {/* Name */}
                            <Field label="Team Name *">
                                <input
                                    className={styles.formInput}
                                    type="text"
                                    placeholder="e.g. Red Hawks"
                                    value={form.name}
                                    onChange={e => updateField("name", e.target.value)}
                                    onKeyDown={e => e.key === "Enter" && submit()}
                                    disabled={isLoading}
                                    autoFocus
                                />
                            </Field>

                            {/* Club — only shown if user has clubs */}
                            {clubs.length > 0 && (
                                <Field label="Club (optional)">
                                    <select
                                        className={styles.formSelect}
                                        value={form.clubId}
                                        onChange={e => updateField("clubId", e.target.value)}
                                        disabled={isLoading}
                                    >
                                        <option value="">— No club —</option>
                                        {clubs.map(c => (
                                            <option key={c.id} value={c.id}>{c.name}</option>
                                        ))}
                                    </select>
                                </Field>
                            )}

                            {/* Sport type — dynamic */}
                            <Field label="Sport (optional)">
                                <select
                                    className={styles.formSelect}
                                    value={form.sportTypeId}
                                    onChange={e => updateField("sportTypeId", e.target.value)}
                                    disabled={isLoading || sportTypesLoading}
                                >
                                    <option value="">
                                        {sportTypesLoading ? "Loading…" : "— Any sport —"}
                                    </option>
                                    {sportTypes.map(s => (
                                        <option key={s.id} value={s.id}>{s.name}</option>
                                    ))}
                                </select>
                            </Field>

                            {/* Error */}
                            {error && <p className={styles.error}>{error}</p>}

                            {/* Submit */}
                            <button
                                className={styles.submitBtn}
                                onClick={submit}
                                disabled={isLoading}
                            >
                                {isLoading ? (
                                    <><Spinner /> Creating…</>
                                ) : "Create Team"}
                            </button>
                        </>
                    )}
                </div>
            </div>
        </div>
    );
}