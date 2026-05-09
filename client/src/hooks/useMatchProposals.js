import { useCallback, useEffect, useState } from "react";

const MATCH_PROPOSALS_ENDPOINT = "/api/matches/proposals";

function readField(source, ...keys) {
    for (const key of keys) {
        if (source?.[key] !== undefined && source?.[key] !== null) {
            return source[key];
        }
    }
    return undefined;
}

function normalizeMatchProposal(raw = {}) {
    const team1Id = readField(raw, "team1_id", "team1Id");
    const team2Id = readField(raw, "team2_id", "team2Id");
    const rawStatus = readField(raw, "status", "status_name", "statusName");
    const team1Contacts = readField(raw, "team1_contacts", "team1Contacts") || [];
    const team2Contacts = readField(raw, "team2_contacts", "team2Contacts") || [];

    return {
        id: readField(raw, "id", "proposal_id", "proposalId"),
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
        team1ClubCity: readField(raw, "team1_club_city", "team1ClubCity") || "",
        team2ClubCity: readField(raw, "team2_club_city", "team2ClubCity") || "",
        team1Contacts,
        team2Contacts,
        original: raw,
    };
}

function normalizeProposalList(payload) {
    const rows = Array.isArray(payload)
        ? payload
        : payload?.proposals ?? payload?.matches ?? payload?.items ?? [];

    return rows.map(normalizeMatchProposal);
}

async function readJson(response) {
    try {
        return await response.json();
    } catch {
        return {};
    }
}

async function fetchMatchProposals(filters = {}) {
    const params = new URLSearchParams();

    if (filters.teamId) {
        params.set("team_id", String(filters.teamId));
    }
    if (filters.weekStartDate) {
        params.set("week_start_date", filters.weekStartDate);
    }
    if (filters.archived) {
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
    const response = await fetch(`${MATCH_PROPOSALS_ENDPOINT}/${proposalId}/status`, {
        method: "PATCH",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status, ...extra }),
    });
    const payload = await readJson(response);

    if (!response.ok) {
        throw new Error(payload?.message || "Failed to update match proposal.");
    }

    return normalizeMatchProposal(payload?.proposal ?? payload?.match ?? payload);
}

export function useMatchProposals(filters = {}) {
    const { teamId, weekStartDate, archived } = filters;
    const [proposals, setProposals] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [submitting, setSubmitting] = useState(false);

    const load = useCallback(async () => {
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
        setSubmitting(true);
        setError("");

        try {
            const updatedProposal = await updateMatchProposalStatus(proposalId, status, extra);
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
        load,
        setProposalStatus,
    };
}
