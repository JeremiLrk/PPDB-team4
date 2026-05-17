// Shared hook for useClub.

import { useEffect, useState } from "react";

function useClub(id) {
    /*
     Loads one club record and keeps it refreshable.
    */
    const [club, setClub] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    useEffect(() => {
        if (!id) return;

        let alive = true;

        async function fetchClub() {
            /*
             Fetches the club record for the active club id.
            */
            try {
                const response = await fetch(`/api/clubs/${id}`);
                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data?.message || "Kon club niet laden.");
                }

                if (alive) {
                    setClub(data.club);
                }
            } catch (err) {
                if (alive) {
                    setError(err.message);
                    setClub(null);
                }
            } finally {
                if (alive) {
                    setLoading(false);
                }
            }
        }

        fetchClub();
        return () => {
            alive = false;
        };
    }, [id]);

    return { club, loading, error };
}

export default useClub;
