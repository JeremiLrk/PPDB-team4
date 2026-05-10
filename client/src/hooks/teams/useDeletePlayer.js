import { useState, useCallback } from "react";

/**
 * useDeletePlayer - manages the confirmation dialog and DELETE request.
 * Supports 2-stage confirmation for minimum roster size violations.
 *
 * @param {{ teamId: number|string, playerId: number|string, onDeleted?: () => void }} options
 */
export function useDeletePlayer({ teamId, playerId, onDeleted } = {}) {
    const [isOpen,         setIsOpen]         = useState(false);
    const [loading,        setLoading]        = useState(false);
    const [error,          setError]          = useState(null);
    const [violateWarning, setViolateWarning] = useState(null);

    const openDialog  = useCallback(() => { setIsOpen(true); setError(null); }, []);
    const closeDialog = useCallback(() => {
        setIsOpen(false);
        setError(null);
        setViolateWarning(null);
    }, []);

    const confirmDelete = useCallback(async (confirmViolate = false) => {
        setLoading(true);
        setError(null);
        setViolateWarning(null);
        try {
            // Build URL with confirmation flag if needed
            let url = `/api/teams/${teamId}/players/${playerId}`;
            if (confirmViolate) {
                url += "?confirmViolate=true";
            }

            const res  = await fetch(url, {
                method: "DELETE",
            });
            const data = await res.json().catch(() => ({}));

            // Handle 202 warning response (minimum roster violation)
            if (res.status === 202 && data.warning === "violates_min_players") {
                setViolateWarning({
                    message: data.message,
                    ladders: data.ladders || []
                });
                setLoading(false);
                return;
            }

            if (!res.ok) throw new Error(data?.message || "Failed to remove player.");
            setIsOpen(false);
            onDeleted?.();
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [teamId, playerId, onDeleted]);

    return {
        isOpen, openDialog, closeDialog, confirmDelete, loading, error,
        violateWarning, setViolateWarning
    };
}
