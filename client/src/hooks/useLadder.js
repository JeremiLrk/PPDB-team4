import { useEffect, useState } from "react";

export function useTeamAchievements(teamId) {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (!teamId) { setLoading(false); return; }
        let alive = true;
        setLoading(true);
        fetch(`/api/teams/${teamId}/achievements`)
            .then(res => {
                if (!res.ok) throw new Error("Failed to fetch achievements");
                return res.json();
            })
            .then(json => { if (alive) { setData(json); setLoading(false); } })
            .catch(err => { if (alive) { setError(err.message); setLoading(false); } });
        return () => { alive = false; };
    }, [teamId]);

    return { data, loading, error };
}

export function useLadderPlayers(clubId, ladderId) {
    const [players, setPlayers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (!clubId || !ladderId) return;

        let alive = true;
        setLoading(true);
        setPlayers([]); 

        fetch(`/api/clubs/${clubId}/ladders/${ladderId}/players`)
            .then(res => {
                if (!res.ok) throw new Error("Failed to fetch players");
                return res.json();
            })
            .then(data => {
                if (alive) {
                    setPlayers(data);
                    setLoading(false);
                }
            })
            .catch(err => {
                if (alive) {
                    setError(err.message);
                    setLoading(false);
                }
            });

        return () => { alive = false; };
    }, [clubId, ladderId]);

    return { players, loading, error };
}

export function useLadder(clubId, ladderId) {
    const [ladder, setLadder] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (!clubId || !ladderId) {
            setLadder(null);
            return;
        }

        let alive = true;
        setLoading(true);

        fetch(`/api/clubs/${clubId}/ladders/${ladderId}/details`)
            .then(res => {
                if (!res.ok) throw new Error("Failed to fetch ladder details");
                return res.json();
            })
            .then(data => {
                if (alive) {
                    setLadder(data);
                    setLoading(false);
                }
            })
            .catch(err => {
                if (alive) {
                    setError(err.message);
                    setLoading(false);
                }
            });

        return () => { alive = false; };
    }, [clubId, ladderId]);

    return { ladder, loading, error };
}
