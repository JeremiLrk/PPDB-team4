// Team management hook for useDeletePlayer.

import { useState, useCallback } from "react";

/**
 * useDeletePlayer - manages the confirmation dialog and DELETE request.
 * Supports 2-stage confirmation for minimum roster size violations.
 *
 * @param {{ teamId: number|string, playerId: number|string, onDeleted?: () => void }} options
 */
export function useDeletePlayer({ teamId, playerId, onDeleted } = {}) {
    /*
     Owns the remove-player confirmation flow for one team member.
    */
    const [isOpen,         setIsOpen]         = useState(false);
    const [loading,        setLoading]        = useState(false);
    const [error,          setError]          = useState(null);
    const [violateWarning, setViolateWarning] = useState(null);

    const openDialog  = useCallback(() => { setIsOpen(true); setError(null); }, []);
    const closeDialog = useCallback(() => {
        /*
         Closes the dialog and clears any warning state.
        */
        setIsOpen(false);
        setError(null);
        setViolateWarning(null);
    }, []);

    const confirmDelete = useCallback(async (confirmDropLadders = false) => {
        /*
         Sends the removal request and optionally confirms ladder fallout.
        */
        setLoading(true);
        setError(null);
        setViolateWarning(null);
        try {
            const res  = await fetch(`/api/teams/${teamId}/players/${playerId}`, {
                method:  "DELETE",
                headers: { "Content-Type": "application/json" },
                body:    JSON.stringify({ confirmDropLadders: confirmDropLadders }),
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
