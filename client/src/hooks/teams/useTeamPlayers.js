// Team management hook for useTeamPlayers.

import { useEffect, useState, useCallback } from "react";


export function useTeamPlayers(teamId) {
    /*
     Loads the player list for one team and supports local inserts.
    */
    const [players, setPlayers] = useState([]);
    const [total,   setTotal]   = useState(null);
    const [loading, setLoading] = useState(false);
    const [error,   setError]   = useState(null);

    const addPlayerLocally = useCallback((player) => {
        /*
         Inserts a player locally when the backend add flow succeeds.
        */
        setPlayers(prev => {
            // duplicate protection
            if (prev.some(p => p.id === player.id)) return prev;
            return [player, ...prev];
        });

        setTotal(prev => (prev ?? 0) + 1);
    }, []);

    const load = useCallback(async () => {
        if (!teamId) return;
        /*
         Fetches the current player list for the active team.
        */
        setLoading(true);
        setError(null);
        try {
            const res  = await fetch(`/api/teams/${teamId}/players`);
            const data = await res.json();
            if (!res.ok) throw new Error(data?.message || "Failed to load players.");
            setPlayers(data.players ?? []);
            setTotal(data.total   ?? 0);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [teamId]);

    useEffect(() => { void load(); }, [load]);

    return {
        players,
        total,
        loading,
        error,
        reload: load,
        addPlayerLocally,
    };
}
