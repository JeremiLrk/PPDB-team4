// Shared hook for useLadder.

import { useEffect, useState } from "react";

export function useTeamAchievements(teamId) {
    /*
     Loads achievement stats for one team.
    */
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    useEffect(() => {
        if (!teamId) { setLoading(false); return; }
        let alive = true;
        setLoading(true);
        /*
         Fetches the team's achievements payload.
        */
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
    /*
     Loads the player list for one ladder.
    */
    const [players, setPlayers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (!clubId || !ladderId) return;

        let alive = true;
        setLoading(true);
        setPlayers([]); 

        /*
         Fetches the ladder ranking rows for the active ladder.
        */
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
    /*
     Loads the ladder detail payload for one ladder page.
    */
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

        /*
         Fetches the ladder detail record for the active ladder.
        */
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
