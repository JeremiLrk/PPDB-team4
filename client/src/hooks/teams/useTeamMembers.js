import { useEffect, useState, useCallback } from "react";

export function useTeamMembers(teamId) {
    const [members, setMembers] = useState([]);
    const [total,   setTotal]   = useState(null);
    const [loading, setLoading] = useState(false);
    const [error,   setError]   = useState(null);

    const load = useCallback(async () => {
        if (!teamId) return;
        setLoading(true);
        setError(null);
        try {
            const res  = await fetch(`/api/teams/${teamId}/members`);
            const data = await res.json();
            if (!res.ok) throw new Error(data?.message || "Failed to load members.");
            setMembers(data.members ?? []);
            setTotal(data.total   ?? 0);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [teamId]);

    useEffect(() => { void load(); }, [load]);

    return {
        members,
        total,
        loading,
        error,
        reload: load,
    };
}
