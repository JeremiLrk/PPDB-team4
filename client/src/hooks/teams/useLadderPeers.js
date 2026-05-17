// Team management hook for useLadderPeers.

import { useState, useCallback } from "react";

/**
 * useLadderPeers
 *
 * Fetches all teams that share a given ladder with `teamId`,
 * excluding `teamId` itself.  Results come back ordered by ladder rank.
 *
 * The fetch is intentionally manual (call `load(teamId, ladderId)`) so the
 * component can choose which ladder to query before firing the request.
 *
 * @returns {{
 *   peers:   Array<{ id, name, clubId, clubName, sportTypeId,
 *                    rank, rating, matchesPlayed }>,
 *   loading: boolean,
 *   error:   string | null,
 *   load:    (teamId: number, ladderId: number) => Promise<void>,
 *   reset:   () => void,
 * }}
 */
export function useLadderPeers() {
    /*
     Loads the list of peer teams that share one ladder.
    */
    const [peers,   setPeers]   = useState([]);
    const [loading, setLoading] = useState(false);
    const [error,   setError]   = useState(null);

    const load = useCallback(async (teamId, ladderId) => {
        if (!teamId || !ladderId) return;

        /*
         Fetches the teams in one ladder, excluding the active team.
        */
        setLoading(true);
        setError(null);
        setPeers([]);

        try {
            const res  = await fetch(
                `/api/teams/${teamId}/ladder-peers?ladder_id=${ladderId}`,
                { credentials: "include" },
            );
            const data = await res.json();

            if (!res.ok) {
                throw new Error(
                    data?.description || data?.message || "Failed to load ladder peers.",
                );
            }

            setPeers(data.peers ?? []);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, []);

    const reset = useCallback(() => {
        /*
         Clears the peer list and its loading/error state.
        */
        setPeers([]);
        setError(null);
        setLoading(false);
    }, []);

    return { peers, loading, error, load, reset };
}
