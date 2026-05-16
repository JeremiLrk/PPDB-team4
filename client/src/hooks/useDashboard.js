import { useEffect, useState } from "react";

const mockDashboardData = {
    roles: ["user"],
    clubs: [],
    pending_requests: {
        my_requests: [],
        my_club_creation_requests: [],
    },
};

export function useDashboard() {
    const [dashboardData, setDashboardData] = useState(mockDashboardData);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        let alive = true;

        async function loadDashboard() {
            try {
                const response = await fetch("/api/me/dashboard", {
                    credentials: "include",
                });

                if (!response.ok) {
                    throw new Error("Dashboard data kon niet geladen worden.");
                }

                const data = await response.json();
                if (alive) {
                    setDashboardData(data);
                    setError("");
                }
            } catch (err) {
                // Fallback to mock keeps frontend flow buildable while backend evolves.
                if (alive) {
                    setDashboardData(mockDashboardData);
                    setError(err?.message || "Onbekende fout bij dashboard laden.");
                }
            } finally {
                if (alive) {
                    setLoading(false);
                }
            }
        }

        loadDashboard();
        return () => {
            alive = false;
        };
    }, []);

    return { dashboardData, loading, error };
}
