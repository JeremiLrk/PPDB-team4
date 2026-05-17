// Team management hook for useRenameTeam.

import { useState } from "react";

/**
 * useRenameTeam - manages the rename panel state and PATCH request.
 * Uses the same step-based API as useCreateTeam:
 *   -1 = closed (idle)
 *   -2 = loading
 *    0 = form open
 *    1 = success
 *
 * @param {{ teamId: number|string, currentName: string, onRenamed?: (team: object) => void }} options
 */
export function useRenameTeam({ teamId, currentName, onRenamed } = {}) {
    /*
     Owns the rename-team panel state and submit flow.
    */
    const [newName, setNewName] = useState("");
    const [step,    setStep]    = useState(-1);
    const [error,   setError]   = useState(null);

    function openPanel() {
        /*
         Opens the panel with an empty draft.
        */
        setNewName("");
        setError(null);
        setStep(0);
    }

    function closePanel() {
        /*
         Closes the panel and clears the draft state.
        */
        setStep(-1);
        setNewName("");
        setError(null);
    }
    async function submit() {
        /*
         Validates and sends the rename request.
        */
        /*
         Validates and sends the rename request.
        */
        const name = newName.trim() || currentName;
        if (!name) return;

        setStep(-2);
        setError(null);

        try {
            const res  = await fetch(`/api/teams/${teamId}`, {
                method:      "PATCH",
                credentials: "include",
                headers:     { "Content-Type": "application/json" },
                body:        JSON.stringify({ name }),
            });
            const data = await res.json().catch(() => ({}));
            if (!res.ok) throw new Error(data?.message || "Failed to rename team.");

            setStep(1);
            onRenamed?.(data.team ?? { name });

            setTimeout(closePanel, 1400);
        } catch (err) {
            setError(err.message);
            setStep(0);
        }
    }

    return {
        newName, setNewName,
        step,
        error,
        openPanel,
        closePanel,
        submit,
        isOpen:    step !== -1,
        isLoading: step === -2,
        isSuccess: step === 1,
    };
}
