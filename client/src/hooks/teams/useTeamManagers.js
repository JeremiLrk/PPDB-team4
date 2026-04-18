import { useEffect, useState, useCallback } from "react";

/**
 * useTeamManagers — loads a list of team managers.
 *
 * Each manager in the list contains standard account fields
 * plus a permissions object { canRename, canDelete, canEditPlayers, canEditManagers }.
 *
 * @param {number|string} teamId
 */
export function useTeamManagers(teamId) {
    const [managers, setManagers] = useState([]);
    const [total,    setTotal]    = useState(null);
    const [loading,  setLoading]  = useState(false);
    const [error,    setError]    = useState(null);

    const load = useCallback(async () => {
        if (!teamId) return;
        setLoading(true);
        setError(null);
        try {
            const res  = await fetch(`/api/teams/${teamId}/managers`, {
                credentials: "include",
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data?.message || "Failed to load managers.");
            setManagers(data.managers ?? []);
            setTotal(data.total ?? 0);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [teamId]);

    useEffect(() => { void load(); }, [load]);

    return {
        managers,
        total,
        loading,
        error,
        reload: load,
    };
}
