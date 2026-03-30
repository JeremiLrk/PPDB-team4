import { useState, useCallback } from "react";

/**
 * useDeletePlayer - manages the confirmation dialog and DELETE request.
 *
 * @param {{ teamId: number|string, playerId: number|string, onDeleted?: () => void }} options
 */
export function useDeletePlayer({ teamId, playerId, onDeleted } = {}) {
    const [isOpen,   setIsOpen]   = useState(false);
    const [loading,  setLoading]  = useState(false);
    const [error,    setError]    = useState(null);

    const openDialog  = useCallback(() => { setIsOpen(true); setError(null); }, []);
    const closeDialog = useCallback(() => { setIsOpen(false); setError(null); }, []);

    const confirmDelete = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const res  = await fetch(`/api/teams/${teamId}/players/${playerId}`, {
                method: "DELETE",
            });
            const data = await res.json().catch(() => ({}));
            if (!res.ok) throw new Error(data?.message || "Failed to remove player.");
            setIsOpen(false);
            onDeleted?.();
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [teamId, playerId, onDeleted]);

    return { isOpen, openDialog, closeDialog, confirmDelete, loading, error };
}
