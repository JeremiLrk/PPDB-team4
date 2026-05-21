// Shared hook for useSportTypes.

import { useEffect, useState } from "react";

export function sortSportTypes(list) {
    /*
     Prioritizes the club focus sports while keeping the rest alphabetical.
    */
    const priority = new Map([
        ["tennis", 0],
        ["padel", 1],
    ]);

    return [...list].sort((left, right) => {
        const leftName = String(left?.name || "");
        const rightName = String(right?.name || "");
        const leftPriority = priority.get(leftName.toLowerCase()) ?? 99;
        const rightPriority = priority.get(rightName.toLowerCase()) ?? 99;

        if (leftPriority !== rightPriority) {
            return leftPriority - rightPriority;
        }

        return leftName.localeCompare(rightName);
    });
}

/**
 * Fetches available sport types from the API.
 * @returns {{ sportTypes: {id: number, name: string}[], loading: boolean, error: string|null }}
 */
export function useSportTypes() {
    /*
     Loads the list of available sport types for select menus.
    */
    const [sportTypes, setSportTypes] = useState([]);
    const [loading, setLoading]       = useState(true);
    const [error, setError]           = useState(null);
    useEffect(() => {
        let alive = true;

        async function load() {
            /*
             Fetches sport types from the backend.
            */
            try {
                const res = await fetch("/api/sport-types", { credentials: "include" });
                if (!res.ok) throw new Error("Failed to load sport types");
                const data = await res.json();
                if (alive) setSportTypes(sortSportTypes(data?.sportTypes ?? []));
            } catch (err) {
                if (alive) setError(err.message);
            } finally {
                if (alive) setLoading(false);
            }
        }

        load();
        return () => { alive = false; };
    }, []);

    return { sportTypes, loading, error };
}
