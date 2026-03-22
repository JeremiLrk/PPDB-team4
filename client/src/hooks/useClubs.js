import { useEffect, useState } from "react";

function useClubs() {
    const [clubs, setClubs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        let alive = true;

        async function loadClubs() {
            try {
                const response = await fetch("/api/clubs");
                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data?.message || "Kon clubs niet laden.");
                }

                if (alive) {
                    setClubs(data?.clubs || []);
                }
            } catch (err) {
                if (alive) {
                    setError(err?.message || "Onbekende fout.");
                }
            } finally {
                if (alive) {
                    setLoading(false);
                }
            }
        }

        loadClubs();

        return () => {
            alive = false;
        };
    }, []);

    return { clubs, loading, error };
}

export default useClubs;