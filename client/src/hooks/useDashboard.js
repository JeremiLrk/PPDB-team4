// Shared hook for useDashboard.

import { useCallback, useEffect, useState } from "react";

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

    const loadDashboard = useCallback(async () => {
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
            setDashboardData(data);
            setError("");
        } catch (err) {
            // Fallback to mock keeps frontend flow buildable while backend evolves.
            setDashboardData(mockDashboardData);
            setError(err?.message || "Onbekende fout bij dashboard laden.");
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        /*
         Fetches the dashboard payload once per hook mount.
        */
        loadDashboard();
    }, [loadDashboard]);

    return { dashboardData, loading, error, reload: loadDashboard };
}
