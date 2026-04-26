import {useCallback, useEffect, useState} from "react";

export function useTeam(teamId) {

    const [loading, setLoading] = useState(true);
    const [error,   setError]   = useState(null);
    const [reloadKey, setReloadKey] = useState(0);
    const [team,    setTeam]    = useState(null);

    const refetch = useCallback(() => setReloadKey(k => k + 1), []);

    useEffect(() => {
        if (!teamId) {
            setLoading(false);
            return;
        }

        const controller = new AbortController();

        async function load() {
            setLoading(true);
            setError(null);
            try {
                const res  = await fetch(`/api/teams/${teamId}`, {
                    signal: controller.signal,
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data?.message || "Team not found.");
                setTeam(data.team);
            } catch (err) {
                if (err.name !== "AbortError") setError(err.message);
            } finally {
                if (!controller.signal.aborted) setLoading(false);
            }
        }

        load();
        return () => controller.abort();
    }, [teamId, reloadKey]);

    return { team, loading, error, refetch };
}
