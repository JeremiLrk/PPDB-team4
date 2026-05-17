import { useState, useEffect, useCallback } from "react";

/**
 * Fetches all disputed matches the current user is authorised to adjudicate.
 * Mirrors the server-side permission check in GET /api/matches/disputed:
 *   - Administrator: sees all disputed matches
 *   - ClubOwner of the ladder's club: sees disputed matches for that ladder
 *   - TeamManager or unauthenticated: receives an empty list or 403
 *
 * @returns {{ matches: object[], total: number, loading: boolean, error: string|null, forbidden: boolean, reload: function }}
 */
export function useDisputedMatches(clubId) {
    const [matches, setMatches]   = useState([]);
    const [total, setTotal]       = useState(0);
    const [loading, setLoading]   = useState(true);
    const [error, setError]       = useState(null);
    const [forbidden, setForbidden] = useState(false);

    const load = useCallback(async () => {
        setLoading(true);
        setError(null);
        setForbidden(false);

        try {
            const params = new URLSearchParams();
            if (clubId) {
                params.set("club_id", String(clubId));
            }
            const res = await fetch(`/api/matches/disputed${params.toString() ? `?${params.toString()}` : ""}`, {
                credentials: "include",
            });

            if (res.status === 401) {
                setForbidden(true);
                return;
            }

            if (res.status === 403) {
                setForbidden(true);
                return;
            }

            const data = await res.json();

            if (!res.ok) {
                throw new Error(data?.message || "Could not load disputed matches.");
            }

            setMatches(data.matches || []);
            setTotal(data.total ?? (data.matches?.length ?? 0));
        } catch (err) {
            setError(err.message || "Could not load disputed matches.");
        } finally {
            setLoading(false);
        }
    }, [clubId]);

    useEffect(() => {
        load();
    }, [load]);

    return { matches, total, loading, error, forbidden, reload: load };
}
