import { useState, useCallback } from "react";

/**
 * useRenameTeam - manages the rename panel and PATCH request.
 *
 * @param {{ teamId: number|string, currentName: string, onRenamed?: (team: object) => void }} options
 */
export function useRenameTeam({ teamId, currentName, onRenamed } = {}) {
    const [isOpen,   setIsOpen]   = useState(false);
    const [newName,  setNewName]  = useState("");
    const [loading,  setLoading]  = useState(false);
    const [error,    setError]    = useState(null);
    const [success,  setSuccess]  = useState(false);

    const openPanel = useCallback(() => {
        setNewName("");
        setError(null);
        setSuccess(false);
        setIsOpen(true);
    }, []);

    const closePanel = useCallback(() => {
        setIsOpen(false);
        setError(null);
        setSuccess(false);
    }, []);

    const submit = useCallback(async () => {
        const name = newName.trim() || currentName;
        if (!name) return;

        setLoading(true);
        setError(null);
        try {
            const res  = await fetch(`/api/teams/${teamId}`, {
                method:  "PATCH",
                headers: { "Content-Type": "application/json" },
                body:    JSON.stringify({ name }),
            });
            const data = await res.json().catch(() => ({}));
            if (!res.ok) throw new Error(data?.message || "Failed to rename team.");
            setSuccess(true);
            onRenamed?.(data.team ?? { name });
            setTimeout(() => setIsOpen(false), 900);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [teamId, newName, currentName, onRenamed]);

    return {
        isOpen, openPanel, closePanel,
        newName, setNewName,
        loading, error, success,
        submit,
    };
}
