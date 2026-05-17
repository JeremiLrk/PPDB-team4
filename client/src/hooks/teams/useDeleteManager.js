// Team management hook for useDeleteManager.

import { useState, useCallback } from "react";

/**
 * useDeleteManager — manages confirmation and DELETE requests to delete a manager.
 *
 * @param {{ teamId: number|string, managerId: number|string, onDeleted?: () => void }} options
 */
export function useDeleteManager({ teamId, managerId, onDeleted } = {}) {
    /*
     Owns the manager removal confirmation state and request.
    */
    const [isOpen,  setIsOpen]  = useState(false);
    const [loading, setLoading] = useState(false);
    const [error,   setError]   = useState(null);

    const openDialog  = useCallback(() => { setIsOpen(true);  setError(null); }, []);
    const closeDialog = useCallback(() => { setIsOpen(false); setError(null); }, []);

    const confirmDelete = useCallback(async () => {
        /*
         Sends the delete request for one manager.
        */
        setLoading(true);
        setError(null);
        try {
            const res  = await fetch(`/api/teams/${teamId}/managers/${managerId}`, {
                method:      "DELETE",
                credentials: "include",
            });
            const data = await res.json().catch(() => ({}));
            if (!res.ok) throw new Error(data?.message || "Failed to remove manager.");
            setIsOpen(false);
            onDeleted?.();
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [teamId, managerId, onDeleted]);

    return { isOpen, openDialog, closeDialog, confirmDelete, loading, error };
}
