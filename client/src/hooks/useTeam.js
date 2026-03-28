import { useEffect, useState } from "react";

export function useTeam(teamId) {
    const [team,    setTeam]    = useState(null);
    const [loading, setLoading] = useState(true);
    const [error,   setError]   = useState(null);

    useEffect(() => {
        if (!teamId) return;
        let alive = true;

        async function load() {
            setLoading(true);
            setError(null);
            try {
                const res  = await fetch(`/api/teams/${teamId}`);
                const data = await res.json();
                if (!res.ok) throw new Error(data?.message || "Team not found.");
                if (alive) setTeam(data.team);
            } catch (err) {
                if (alive) setError(err.message);
            } finally {
                if (alive) setLoading(false);
            }
        }

        load();
        return () => { alive = false; };
    }, [teamId]);

    return { team, loading, error };
}
