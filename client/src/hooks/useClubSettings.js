import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useSportTypes } from "@/hooks/useSportTypes.js"

export function useClubSettings(clubId, texts = {}) {
    const navigate = useNavigate();

    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const { sportTypes } = useSportTypes();

    const [club, setClub] = useState(null);
    const [formData, setFormData] = useState({
        name: "",
        description: "",
        city: "",
        sport_type_id: "", 
    });

    const [members, setMembers] = useState([]);
    const [ladders, setLadders] = useState([]);
    const [owners, setOwners] = useState([]);
    
    // --- ADDED: Eligible Teams State ---
    const [eligibleTeams, setEligibleTeams] = useState([]);

    const [ratingFunctions, setRatingFunctions] = useState([]);
    const [ruleSets, setRuleSets] = useState([]);

    const [updating, setUpdating] = useState(false);
    const [updateMessage, setUpdateMessage] = useState(null);

    const [activeTab, setActiveTab] = useState("general");

    useEffect(() => {
        async function fetchClubData() {
            try {
                // Included the new eligible-teams endpoint in the initial load
                const [clubRes, membersRes, ownersRes, laddersRes, ratingsRes, rulesRes, teamsRes] = await Promise.all([
                    fetch(`/api/clubs/${clubId}`, { credentials: "include" }),
                    fetch(`/api/clubs/${clubId}/members`, { credentials: "include" }),
                    fetch(`/api/clubs/${clubId}/owners`, { credentials: "include" }),
                    fetch(`/api/clubs/${clubId}/ladders`, { credentials: "include" }),
                    fetch(`/api/rating-functions`), 
                    fetch(`/api/rule-sets`),
                    fetch(`/api/clubs/${clubId}/eligible-teams`, { credentials: "include" })
                ]);

                const clubData = await clubRes.json();
                const membersData = await membersRes.json();
                const ownersData = await ownersRes.json();
                const laddersData = await laddersRes.json();
                const ratingsData = await ratingsRes.json();
                const rulesData = await rulesRes.json();
                const teamsData = await teamsRes.json();

                if (!clubRes.ok) throw new Error(clubData.message);

                setClub(clubData.club);
                
                setFormData({
                    name: clubData.club.name || "",
                    description: clubData.club.description || "",
                    city: clubData.club.city || "",
                    sport_type_id: clubData.club.sport_type_id || "",
                });

                setMembers(membersData.members || []);
                setOwners(ownersData.owners || []);
                setLadders(Array.isArray(laddersData) ? laddersData : (laddersData.ladders || []));
                setRatingFunctions(ratingsData.ratingFunctions || []);
                setRuleSets(rulesData.ruleSets || []);
                setEligibleTeams(teamsData.teams || []);

            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        }

        if (clubId) fetchClubData();
    }, [clubId]);

    const handleChange = (e) => {
        setFormData(prev => ({
            ...prev,
            [e.target.name]: e.target.value,
        }));
    };

    const updateClub = async (e) => {
        e.preventDefault();
        setUpdating(true);
        setUpdateMessage(null);

        try {
            const res = await fetch(`/api/clubs/${clubId}`, {
                method: "PUT",
                credentials: "include",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(formData),
            });

            const data = await res.json();
            if (!res.ok) throw new Error(data.message);

            setClub(prev => ({ ...prev, ...formData }));
            setUpdateMessage({ type: "success", text: texts.saved_successfully || "Saved successfully" });
        } catch (err) {
            setUpdateMessage({ type: "error", text: err.message || texts.could_not_save_club || "Could not save club." });
        } finally {
            setUpdating(false);
        }
    };

    const createLadder = async (ladderData) => {
        try {
            const res = await fetch(`/api/clubs/${clubId}/ladders`, {
                method: "POST",
                credentials: "include",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(ladderData),
            });

            const data = await res.json();

            if (!res.ok) throw new Error(data.message);

            setLadders(prev => [...prev, data.ladder]);
        } catch (err) {
            setError(err.message || texts.could_not_create_ladder || "Could not create ladder.");
        }
    };

    const addMember = async (email) => {
        try {
            const res = await fetch(`/api/clubs/${clubId}/members`, {
                method: "POST",
                credentials: "include",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ email }),
            });

            const data = await res.json();

            if (!res.ok) throw new Error(data.message);

            setMembers(prev => [...prev, data.Member]);
        } catch (err) {
            setError(err.message || texts.could_not_add_member || "Could not add member.");
        }
    };

    const removeMember = async (MemberId) => {
        try {
            const res = await fetch(`/api/clubs/${clubId}/members/${MemberId}`, {
                method: "DELETE",
                credentials: "include",
            });

            if (!res.ok) throw new Error("Failed to remove Member");

            setMembers(prev => prev.filter(p => p.id !== MemberId));
        } catch (err) {
            setError(err.message || texts.could_not_remove_member || "Could not remove member.");
        }
    };

    const addOwner = async (ownerId) => {
        try {
            const res = await fetch(`/api/clubs/${clubId}/owners`, {
                method: "POST",
                credentials: "include",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ owner_id: ownerId }),
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.message);

            // Refresh owners list or append the new one
            setOwners(prev => [...prev, data.owner]);
        } catch (err) {
            setError(err.message || texts.could_not_add_owner || "Could not add owner.");
        }
    };

    const removeOwner = async (ownerId) => {
        try {
            const res = await fetch(`/api/clubs/${clubId}/owners/${ownerId}`, {
                method: "DELETE",
                credentials: "include",
            });
            if (!res.ok) {
                const data = await res.json();
                throw new Error(data.message);
            }
            setOwners(prev => prev.filter(o => o.id !== ownerId));
        } catch (err) {
            alert(err.message || texts.could_not_remove_owner || "Could not remove owner."); // Use alert for specific owner errors (like self-deletion)
        }
    };

    const searchAccounts = async (query) => {
        if (!query || query.length < 3) return [];
        
        try {
            const res = await fetch(`/api/accounts/search?q=${encodeURIComponent(query)}`, {
                credentials: "include"
            });
            const data = await res.json();
            return data.accounts || [];
        } catch (err) {
            console.error("Search failed", err);
            return [];
        }
    };

    const addTeamToLadder = async (ladderId, teamId) => {
        try {
            const res = await fetch(`/api/clubs/${clubId}/ladders/${ladderId}/teams/${teamId}`, {
                method: "POST",
                credentials: "include",
            });

            if (!res.ok) {
                const data = await res.json();
                throw new Error(data.message || "Could not add team to ladder.");
            }
            
        } catch (err) {
            alert(err.message);
        }
    };


    return {
        loading,
        error,

        activeTab,
        setActiveTab,

        updating,
        updateMessage,

        club,
        formData,
        handleChange,
        updateClub,

        members,
        addMember,
        removeMember,

        owners,
        addOwner,
        removeOwner,
        searchAccounts,

        ladders,
        createLadder,

        ratingFunctions,
        ruleSets,
        sportTypes,

        eligibleTeams,
        addTeamToLadder,

        goBack: () => navigate("/dashboard"),
    };
}
