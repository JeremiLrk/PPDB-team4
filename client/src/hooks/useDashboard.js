// Shared hook for useDashboard.

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
    /*
     Loads and stores the dashboard payload for the active session.
    */
    const [dashboardData, setDashboardData] = useState(mockDashboardData);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        /*
         Fetches the dashboard payload once per hook mount.
        */
        let alive = true;

        async function loadDashboard() {
            /*
             Requests the dashboard endpoint and stores the response when mounted.
            */
            try {
                // TODO(team): replace this with the real API contract once auth/roles are finalized.
                const response = await fetch("/api/me/dashboard", {
                    credentials: "include",
                });
/* 
                if (!response.ok) {
                    throw new Error("Dashboard data kon niet geladen worden.");
                } */

                const data = await response.json();
                if (alive) {
                    // Keep the latest dashboard payload only while this hook instance is still mounted.
                    setDashboardData(data);
                    setError("");
                }
            } catch (err) {
                // Fallback to mock keeps frontend flow buildable while backend evolves.
                if (alive) {
                    // Fall back to the stub payload instead of breaking the whole dashboard shell.
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
