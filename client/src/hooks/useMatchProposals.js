import { useCallback, useEffect, useState } from "react";
import {
    fetchMatchProposals,
    updateMatchProposalStatus,
} from "@/api/matches.js";

export function useMatchProposals(filters = {}) {
    const { teamId, weekStartDate } = filters;
    const [proposals, setProposals] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [submitting, setSubmitting] = useState(false);

    const load = useCallback(async () => {
        setLoading(true);
        setError("");

        try {
            const loadedProposals = await fetchMatchProposals({ teamId, weekStartDate });
            setProposals(loadedProposals);
        } catch (err) {
            setError(err?.message || "Failed to load match proposals.");
        } finally {
            setLoading(false);
        }
    }, [teamId, weekStartDate]);

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
