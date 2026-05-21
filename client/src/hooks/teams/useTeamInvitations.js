// Team management hook for useTeamInvitations.

import { useState, useEffect } from "react";

export function useTeamInvitations() {
    /*
     Loads and mutates the current user's team invitations.
    */
    const [invitations, setInvitations] = useState([]);
    const [clubInvitations, setClubInvitations] = useState([]);
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
            const [teamResponse, clubResponse] = await Promise.all([
                fetch("/api/teams/my-join-requests", { credentials: "include" }),
                fetch("/api/teams/my-club-invitations", { credentials: "include" }),
            ]);
            if (!teamResponse.ok || !clubResponse.ok) throw new Error("Failed to fetch");
            const teamData = await teamResponse.json();
            const clubData = await clubResponse.json();
            setInvitations(Array.isArray(teamData.joinRequests) ? teamData.joinRequests : []);
            setClubInvitations(Array.isArray(clubData.clubInvitations) ? clubData.clubInvitations : []);
        } catch (err) {
            setError(err.message);
            setInvitations([]);
            setClubInvitations([]);
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
                { method: "POST", credentials: "include" }
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
                { method: "POST", credentials: "include" }
            );
            if (!response.ok) throw new Error("Failed to reject");
            setInvitations(prev => prev.filter(inv => inv.id !== invitationId));
            return true;
        } catch (err) {
            setError(err.message);
            return false;
        }
    }

    async function acceptClubInvitation(invitationId, teamId) {
        /*
         Accepts one club/ladder invitation for a managed team.
        */
        try {
            const response = await fetch(
                `/api/teams/${teamId}/club-invitations/${invitationId}/accept`,
                { method: "POST", credentials: "include" }
            );
            if (!response.ok) throw new Error("Failed to accept");
            setClubInvitations(prev => prev.filter(inv => inv.id !== invitationId));
            return true;
        } catch (err) {
            setError(err.message);
            return false;
        }
    }

    async function rejectClubInvitation(invitationId, teamId) {
        /*
         Rejects one club/ladder invitation for a managed team.
        */
        try {
            const response = await fetch(
                `/api/teams/${teamId}/club-invitations/${invitationId}/reject`,
                { method: "POST", credentials: "include" }
            );
            if (!response.ok) throw new Error("Failed to reject");
            setClubInvitations(prev => prev.filter(inv => inv.id !== invitationId));
            return true;
        } catch (err) {
            setError(err.message);
            return false;
        }
    }

    return {
        invitations,
        clubInvitations,
        loading,
        error,
        acceptInvitation,
        rejectInvitation,
        acceptClubInvitation,
        rejectClubInvitation,
    };
}
