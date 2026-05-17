// Shared hook for usePlayedMatches.

import { useEffect, useState } from "react";

function normalizePlayedMatch(raw = {}) {
    /*
     Normalizes one played-match row for the club-home summary.
    */
    return {
        id: raw.id,
        team1Name: raw.team1Name || raw.team1_name || "Team 1",
        team2Name: raw.team2Name || raw.team2_name || "Team 2",
        played: raw.played || null,
    };
}

export function usePlayedMatches(limit = 3) {
    /*
     Loads a small list of recently played matches.
    */
    const [matches, setMatches] = useState([]);
    const [loading, setLoading] = useState(true);
    useEffect(() => {
        let alive = true;

        async function fetchPlayedMatches() {
            /*
             Fetches recently played matches for the current view.
            */
            try {
                const response = await fetch(`/api/matches/played?from=0&to=${limit}`);
                const payload = await response.json().catch(() => ({}));

                if (!response.ok) {
                    throw new Error(payload?.message || "Failed to load played matches.");
                }

                const rows = Array.isArray(payload?.matches) ? payload.matches : [];
                if (alive) {
                    setMatches(rows.map(normalizePlayedMatch));
                }
            } catch {
                if (alive) {
                    setMatches([]);
                }
            } finally {
                if (alive) {
                    setLoading(false);
                }
            }
        }

        fetchPlayedMatches();
        return () => {
            alive = false;
        };
    }, [limit]);

    return { matches, loading };
}

export default usePlayedMatches;
