// Shared hook for useClubHomeSummary.

import { useEffect, useState } from "react";

function readField(source, ...keys) {
    /*
     Reads the first available field from a payload shape.
    */
    for (const key of keys) {
        if (source?.[key] !== undefined && source?.[key] !== null) {
            return source[key];
        }
    }
    return undefined;
}

function normalizeMatch(raw = {}) {
    /*
     Normalizes a club-home match row from mixed backend shapes.
    */
    return {
        id: readField(raw, "id"),
        team1Id: readField(raw, "team1Id", "team1_id"),
        team2Id: readField(raw, "team2Id", "team2_id"),
        team1Name: readField(raw, "team1Name", "team1_name") || "Team 1",
        team2Name: readField(raw, "team2Name", "team2_name") || "Team 2",
        team1ClubName: readField(raw, "team1ClubName", "team1_club_name") || "",
        team2ClubName: readField(raw, "team2ClubName", "team2_club_name") || "",
        ladderId: readField(raw, "ladderId", "ladder_id"),
        ladderName: readField(raw, "ladderName", "ladder_name") || "",
        status: readField(raw, "status") || "",
        scoreStatus: readField(raw, "scoreStatus", "score_status") || "",
        proposedStartAt: readField(raw, "proposedStartAt", "proposed_start_at") || "",
        proposedEndAt: readField(raw, "proposedEndAt", "proposed_end_at") || "",
        weekStartDate: readField(raw, "weekStartDate", "week_start_date") || "",
        playedAt: readField(raw, "playedAt", "played_at") || "",
        scoreTeam1: readField(raw, "scoreTeam1", "score_team1"),
        scoreTeam2: readField(raw, "scoreTeam2", "score_team2"),
        rating: readField(raw, "rating"),
    };
}

function normalizePerformer(raw = {}) {
    /*
     Normalizes one performer row from the summary payload.
    */
    return {
        id: readField(raw, "id"),
        name: readField(raw, "name") || "Unknown",
        rating: readField(raw, "rating") ?? 0,
        ladderId: readField(raw, "ladderId", "ladder_id"),
        ladderName: readField(raw, "ladderName", "ladder_name") || "",
    };
}

export function useClubHomeSummary(clubId) {
    /*
     Loads the club-home summary payload and exposes it in UI-friendly form.
    */
    const [summary, setSummary] = useState({
        club: null,
        ladders: [],
        performers: [],
        upcomingMatches: [],
        latestResults: [],
    });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    useEffect(() => {
        if (!clubId) {
            setSummary({
                club: null,
                ladders: [],
                performers: [],
                upcomingMatches: [],
                latestResults: [],
            });
            setLoading(false);
            return;
        }

        let alive = true;
        async function loadSummary() {
            /*
             Fetches the summary payload for the active club.
            */
            setLoading(true);
            setError("");
            setSummary({
                club: null,
                ladders: [],
                performers: [],
                upcomingMatches: [],
                latestResults: [],
            });

            try {
                const response = await fetch(`/api/clubs/${clubId}/home-summary`);
                const payload = await response.json();

                if (!response.ok) {
                    throw new Error(payload?.message || "Failed to load club overview.");
                }

                if (!alive) {
                    return;
                }

                setSummary({
                    club: payload.club || null,
                    ladders: Array.isArray(payload.ladders) ? payload.ladders : [],
                    performers: Array.isArray(payload.performers) ? payload.performers.map(normalizePerformer) : [],
                    upcomingMatches: Array.isArray(payload.upcoming_matches)
                        ? payload.upcoming_matches.map(normalizeMatch)
                        : [],
                    latestResults: Array.isArray(payload.latest_results)
                        ? payload.latest_results.map(normalizeMatch)
                        : [],
                });
            } catch (err) {
                if (alive) {
                    setError(err?.message || "Failed to load club overview.");
                }
            } finally {
                if (alive) {
                    setLoading(false);
                }
            }
        }

        loadSummary();
        return () => {
            alive = false;
        };
    }, [clubId]);

    return { summary, loading, error };
}
