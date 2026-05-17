// Shared hook for useMatchProposals.

import { useCallback, useEffect, useState } from "react";

const MATCH_PROPOSALS_ENDPOINT = "/api/matches/proposals";

function readField(source, ...keys) {
    /*
     Reads the first available field from mixed API payload shapes.
    */
    for (const key of keys) {
        if (source?.[key] !== undefined && source?.[key] !== null) {
            return source[key];
        }
    }
    return undefined;
}

function normalizeMatchProposal(raw = {}) {
    /*
     Normalizes one proposal row into the UI shape used by the cards.
    */
    const team1Id = readField(raw, "team1_id", "team1Id");
    const team2Id = readField(raw, "team2_id", "team2Id");
    const rawStatus = readField(raw, "status", "status_name", "statusName");
    const team1Contacts = readField(raw, "team1_contacts", "team1Contacts") || [];
    const team2Contacts = readField(raw, "team2_contacts", "team2Contacts") || [];
    const scoreSubmissions = readField(raw, "score_submissions", "scoreSubmissions") || [];

    return {
        id: readField(raw, "id", "proposal_id", "proposalId"),
        proposedByUserId: readField(raw, "proposed_by_user_id", "proposedByUserId"),
        acceptedByUserId: readField(raw, "accepted_by_user_id", "acceptedByUserId"),
        acceptanceStatus: readField(raw, "acceptance_status", "acceptanceStatus"),
        team1Id,
        team2Id,
        team1Name:
            readField(raw, "team1_name", "team1Name") ||
            (team1Id ? `Team #${team1Id}` : "Team 1"),
        team2Name:
            readField(raw, "team2_name", "team2Name") ||
            (team2Id ? `Team #${team2Id}` : "Team 2"),
        status: rawStatus?.name ?? rawStatus ?? "pending",
        proposedStartAt: readField(raw, "proposed_start_at", "proposedStartAt", "start_at", "startAt"),
        proposedEndAt: readField(raw, "proposed_end_at", "proposedEndAt", "end_at", "endAt"),
        weekStartDate: readField(raw, "week_start_date", "weekStartDate"),
        team1ClubId: readField(raw, "team1_club_id", "team1ClubId"),
        team2ClubId: readField(raw, "team2_club_id", "team2ClubId"),
        team1ClubName: readField(raw, "team1_club_name", "team1ClubName") || "",
        team2ClubName: readField(raw, "team2_club_name", "team2ClubName") || "",
        team1ClubCity: readField(raw, "team1_club_city", "team1ClubCity") || "",
        team2ClubCity: readField(raw, "team2_club_city", "team2ClubCity") || "",
        team1Contacts,
        team2Contacts,
        scoreStatus: readField(raw, "score_status", "scoreStatus") || "not_submitted",
        scoreSubmissions,
        // Keep the raw payload around so the UI can still inspect anything
        // new the backend starts returning before this hook is extended.
        original: raw,
    };
}

function normalizeProposalList(payload) {
    /*
     Normalizes whatever proposal list wrapper the backend returns.
    */
    const rows = Array.isArray(payload)
        ? payload
        : payload?.proposals ?? payload?.matches ?? payload?.items ?? [];

    return rows.map(normalizeMatchProposal);
}

async function readJson(response) {
    /*
     Reads a JSON body and falls back to an empty object on parse errors.
    */
    try {
        return await response.json();
    } catch {
        return {};
    }
}

async function fetchMatchProposals(filters = {}) {
    const params = new URLSearchParams();

    /*
     Builds the proposal list query string from the active filters.
    */
    if (filters.teamId) {
        params.set("team_id", String(filters.teamId));
    }
    if (filters.weekStartDate) {
        params.set("week_start_date", filters.weekStartDate);
    }
    if (filters.archived) {
        // Archived mode is an explicit opt-in so the default list stays short.
        params.set("archived", "1");
    }

    const queryString = params.toString();
    const response = await fetch(
        `${MATCH_PROPOSALS_ENDPOINT}${queryString ? `?${queryString}` : ""}`,
        { credentials: "include" },
    );
    const payload = await readJson(response);

    if (!response.ok) {
        throw new Error(payload?.message || "Failed to load match proposals.");
    }

    return normalizeProposalList(payload);
}

async function updateMatchProposalStatus(proposalId, status, extra = {}) {
    /*
     Sends one proposal status change through the canonical backend endpoint.
    */
    const response = await fetch(`${MATCH_PROPOSALS_ENDPOINT}/${proposalId}/status`, {
        method: "PATCH",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status, ...extra }),
    });
    const payload = await readJson(response);

    if (!response.ok) {
        throw new Error(payload?.description || payload?.message || "Failed to update match proposal.");
    }

    return normalizeMatchProposal(payload?.proposal ?? payload?.match ?? payload);
}

export function useMatchProposals(filters = {}) {
    const { teamId, weekStartDate, archived } = filters;
    /*
     Loads and updates the match proposal list for the current filters.
    */
    const [proposals, setProposals] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [submitting, setSubmitting] = useState(false);

    const load = useCallback(async () => {
        /*
         Reloads proposals from the backend and replaces the current list.
        */
        setLoading(true);
        setError("");

        try {
            const loadedProposals = await fetchMatchProposals({ teamId, weekStartDate, archived });
            setProposals(loadedProposals);
        } catch (err) {
            setError(err?.message || "Failed to load match proposals.");
        } finally {
            setLoading(false);
        }
    }, [teamId, weekStartDate, archived]);

    const setProposalStatus = useCallback(async (proposalId, status, extra = {}) => {
        /*
         Updates one proposal and patches the local list with the response.
        */
        setSubmitting(true);
        setError("");

        try {
            const updatedProposal = await updateMatchProposalStatus(proposalId, status, extra);
            // Replace only the changed proposal so list position and filters stay stable.
            setProposals((previous) =>
                previous.map((proposal) =>
                    proposal.id === proposalId ? updatedProposal : proposal,
                ),
            );
            return updatedProposal;
        } catch (err) {
            setError(err?.message || "Failed to update match proposal.");
            throw err;
        } finally {
            setSubmitting(false);
        }
    }, []);
    useEffect(() => {
        void load();
    }, [load]);

    return {
        proposals,
        loading,
        error,
        submitting,
        // The tab uses load() for manual refresh and setProposalStatus() for
        // button-driven changes from the proposal cards.
        load,
        setProposalStatus,
    };
}
