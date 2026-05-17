// Shared hook for useWeather.

import { useEffect, useState } from "react";

export function useWeather(club_id, targetDate = "") {
    /*
     Loads weather data for one club/date combination.
    */
    const [weather, setWeather] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    useEffect(() => {
        if (!club_id) {
            setWeather(null);
            setLoading(false);
            setError(null);
            return undefined;
        }

        setLoading(true);
        setError(null);

        const controller = new AbortController();
        const params = new URLSearchParams();
        if (targetDate) {
            params.set("target_dt", targetDate);
        }

        fetch(`/api/weather/${club_id}${params.toString() ? `?${params.toString()}` : ""}`, {
            signal: controller.signal,
        })
            .then((res) => {
                /*
                 Treats a 404 as "no weather available" instead of a hard error.
                */
                if (res.status === 404) {
                    return null;
                }
                if (!res.ok) throw new Error("Failed to fetch weather");
                return res.json();
            })
            .then((data) => {
                setWeather(data);
                setLoading(false);
            })
            .catch((err) => {
                if (err?.name === "AbortError") {
                    return;
                }
                setError(err.message);
                setWeather(null);
                setLoading(false);
            });
        return () => controller.abort();
    }, [club_id, targetDate]);

    return { weather, loading, error };
}
