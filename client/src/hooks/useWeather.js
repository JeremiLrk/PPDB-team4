import { useEffect, useState } from "react";

export function useWeather(club_id) {
    const [weather, setWeather] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (!club_id) return;

        setLoading(true);
        
        fetch(`/api/weather/${club_id}`)
            .then((res) => {
                if (!res.ok) throw new Error("Failed to fetch weather");
                return res.json();
            })
            .then((data) => {
                setWeather(data);
                setLoading(false);
            })
            .catch((err) => {
                setError(err.message);
                setLoading(false);
            });
    }, [club_id]);

    return { weather, loading, error };
}