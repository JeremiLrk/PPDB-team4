import { useEffect, useState } from "react";

export function useWeather(city) {
    const [weather, setWeather] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (!city) return;

        setLoading(true);
        
        fetch(`/api/weather/${encodeURIComponent(city)}`)
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
    }, [city]);

    return { weather, loading, error };
}