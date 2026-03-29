import { useEffect, useState, useCallback } from "react";


export function useTeamPlayers(teamId) {
    const [players, setPlayers] = useState([]);
    const [total,   setTotal]   = useState(null);
    const [loading, setLoading] = useState(false);
    const [error,   setError]   = useState(null);

    const addPlayerLocally = useCallback((player) => {
        setPlayers(prev => {
            // захист від дублювання
            if (prev.some(p => p.id === player.id)) return prev;
            return [player, ...prev];
        });

        setTotal(prev => (prev ?? 0) + 1);
    }, []);

    const load = useCallback(async () => {
        if (!teamId) return;
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
