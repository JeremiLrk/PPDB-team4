import { useEffect, useState } from "react";

export function useMyClubs() {
    const [clubs, setClubs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        let alive = true;

        async function load() {
            try {
                const res = await fetch("/api/clubs/my", { credentials: "include" });
                const data = await res.json();

                if (!res.ok) throw new Error(data?.message || "Could not load clubs.");

                if (alive) setClubs(data?.clubs || []);
            } catch (err) {
                if (alive) setError(err?.message || "Unknown error.");
            } finally {
                if (alive) setLoading(false);
            }
        }

        load();
        return () => { alive = false; };
    }, []);

    return { clubs, loading, error };
}
