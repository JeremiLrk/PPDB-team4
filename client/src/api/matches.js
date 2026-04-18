const MATCH_PROPOSALS_ENDPOINT = "/api/matches/proposals";

function readField(source, ...keys) {
    for (const key of keys) {
        if (source?.[key] !== undefined && source?.[key] !== null) {
            return source[key];
        }
    }
    return undefined;
}

export function normalizeMatchProposal(raw = {}) {
    const team1Id = readField(raw, "team1_id", "team1Id");
    const team2Id = readField(raw, "team2_id", "team2Id");
    const rawStatus = readField(raw, "status", "status_name", "statusName");

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
        location: readField(raw, "location", "venue") || "",
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

export async function fetchMatchProposals(filters = {}) {
    const params = new URLSearchParams();

    if (filters.teamId) {
        params.set("team_id", String(filters.teamId));
    }
    if (filters.weekStartDate) {
        params.set("week_start_date", filters.weekStartDate);
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

export async function updateMatchProposalStatus(proposalId, status, extra = {}) {
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
