import { useEffect, useState } from "react";

/**
 * Fetches available sport types from the API.
 * @returns {{ sportTypes: {id: number, name: string}[], loading: boolean, error: string|null }}
 */
export function useSportTypes() {
    const [sportTypes, setSportTypes] = useState([]);
    const [loading, setLoading]       = useState(true);
    const [error, setError]           = useState(null);

    useEffect(() => {
        let alive = true;

        async function load() {
            try {
                const res = await fetch("/api/sport-types", { credentials: "include" });
                if (!res.ok) throw new Error("Failed to load sport types");
                const data = await res.json();
                if (alive) setSportTypes(data?.sportTypes ?? []);
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
