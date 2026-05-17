// Team management hook for useTeamInvitations.

import { useState, useEffect } from "react";

export function useTeamInvitations() {
    /*
     Loads and mutates the current user's team invitations.
    */
    const [invitations, setInvitations] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    useEffect(() => {
        fetchInvitations();
    }, []);

    async function fetchInvitations() {
        /*
         Fetches the pending team invitation list.
        */
        try {
            setLoading(true);
            setError(null);
            const response = await fetch("/api/teams/my-join-requests");
            if (!response.ok) throw new Error("Failed to fetch");
            const data = await response.json();
            setInvitations(Array.isArray(data.joinRequests) ? data.joinRequests : []);
        } catch (err) {
            setError(err.message);
            setInvitations([]);
        } finally {
            setLoading(false);
        }
    }

    async function acceptInvitation(invitationId, teamId) {
        /*
         Accepts one invitation and removes it from the local list.
        */
        try {
            const response = await fetch(
                `/api/teams/${teamId}/players/join-requests/${invitationId}/accept`,
                { method: "POST" }
            );
            if (!response.ok) throw new Error("Failed to accept");
            setInvitations(prev => prev.filter(inv => inv.id !== invitationId));
            return true;
        } catch (err) {
            setError(err.message);
            return false;
        }
    }

    async function rejectInvitation(invitationId, teamId) {
        /*
         Rejects one invitation and removes it from the local list.
        */
        try {
            const response = await fetch(
                `/api/teams/${teamId}/players/join-requests/${invitationId}/reject`,
                { method: "POST" }
            );
            if (!response.ok) throw new Error("Failed to reject");
            setInvitations(prev => prev.filter(inv => inv.id !== invitationId));
            return true;
        } catch (err) {
            setError(err.message);
            return false;
        }
    }

    return {
        invitations,
        loading,
        error,
        acceptInvitation,
        rejectInvitation,
    };
}
