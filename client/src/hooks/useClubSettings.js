// Shared hook for useClubSettings.

import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useSportTypes } from "@/hooks/useSportTypes.js"

export function useClubSettings(clubId, texts = {}) {
    const navigate = useNavigate();
    /*
     Loads and edits the club settings workspace state.
    */

    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const { sportTypes } = useSportTypes();

    const [club, setClub] = useState(null);
    const [formData, setFormData] = useState({
        name: "",
        description: "",
        city: "",
        sport_type_id: "", // Matches the name attribute in our select
    });
    const [citySelection, setCitySelection] = useState(null);

    const [members, setMembers] = useState([]);
    const [ladders, setLadders] = useState([]);
    const [owners, setOwners] = useState([]);
    const [eligibleTeams, setEligibleTeams] = useState([]);

    const [ratingFunctions, setRatingFunctions] = useState([]);
    const [ruleSets, setRuleSets] = useState([]);

    const [updating, setUpdating] = useState(false);
    const [updateMessage, setUpdateMessage] = useState(null);

    const [activeTab, setActiveTab] = useState("general");

    useEffect(() => {
        async function fetchClubData() {
            /*
             Loads the club settings payload and the related lists.
            */
            try {
                const [clubRes, membersRes, ownersRes, laddersRes, ratingsRes, rulesRes, teamsRes] = await Promise.all([
                    fetch(`/api/clubs/${clubId}`, { credentials: "include" }),
                    fetch(`/api/clubs/${clubId}/members`, { credentials: "include" }),
                    fetch(`/api/clubs/${clubId}/owners`, { credentials: "include" }),
                    fetch(`/api/clubs/${clubId}/ladders`, { credentials: "include" }),
                    fetch(`/api/rating-functions`), 
                    fetch(`/api/rule-sets`),
                    fetch(`/api/clubs/${clubId}/eligible-teams`, { credentials: "include" }),
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
                setCitySelection(clubData.club.city ? { label: clubData.club.city } : null);

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
        /*
         Updates one general-settings form field.
        */
        setFormData(prev => ({
            ...prev,
            [e.target.name]: e.target.value,
        }));
        if (e.target.name === "city") {
            setCitySelection(null);
        }
    };

    const handleCitySelect = (city) => {
        /*
         Copies the selected city suggestion into the settings form.
        */
        setFormData((prev) => ({
            ...prev,
            city: city.label,
        }));
        setCitySelection(city);
    };
    const updateClub = async (e) => {
        /*
         Submits the general club settings form.
        */
        e.preventDefault();
        setUpdating(true);
        setUpdateMessage(null);

        const selectedCity = citySelection?.label?.trim();
        if (!selectedCity) {
            setUpdateMessage({
                type: "error",
                text: texts.city_selection_required || "Please choose a real city from the suggestions.",
            });
            setUpdating(false);
            return;
        }

        try {
            const payload = {
                ...formData,
                city: selectedCity,
            };

            const res = await fetch(`/api/clubs/${clubId}`, {
                method: "PUT",
                credentials: "include",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });

            const data = await res.json();
            if (!res.ok) throw new Error(data.message);

            setClub(prev => ({ ...prev, ...payload }));
            setUpdateMessage({ type: "success", text: texts.saved_successfully || "Saved successfully" });
        } catch (err) {
            setUpdateMessage({ type: "error", text: err.message || texts.could_not_save_club || "Could not save club." });
        } finally {
            setUpdating(false);
        }
    };

    const createLadder = async (ladderData) => {
        /*
         Creates one ladder inside the current club.
        */
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

    const addTeamToLadder = async (ladderId, teamId) => {
        /*
         Adds one team to one ladder.
        */
        try {
            const res = await fetch(`/api/clubs/${clubId}/ladders/${ladderId}/teams/${teamId}`, {
                method: "POST",
                credentials: "include",
            });

            const data = await res.json();
            if (!res.ok) throw new Error(data.message);

            return data;
        } catch (err) {
            setError(err.message || texts.could_not_add_team_to_ladder || "Could not add team to ladder.");
            throw err;
        }
    };

    const addMember = async (email) => {
        /*
         Adds one club member by email.
        */
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
        /*
         Removes one club member from the club.
        */
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
        /*
         Adds one club owner.
        */
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

    const deleteClub = async () => {
        try {
            const res = await fetch(`/api/clubs/${clubId}`, {
                method: "DELETE",
                credentials: "include",
            });

            const data = await res.json().catch(() => ({}));
            if (!res.ok) {
                throw new Error(data.message || texts.could_not_delete_club || "Could not delete club.");
            }

            navigate("/dashboard");
        } catch (err) {
            setError(err.message || texts.could_not_delete_club || "Could not delete club.");
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
        handleCitySelect,
        updateClub,

        members,
        addMember,
        removeMember,

        owners,
        addOwner,
        removeOwner,
        searchAccounts,
        deleteClub,

        ladders,
        createLadder,
        eligibleTeams,
        addTeamToLadder,

        ratingFunctions,
        ruleSets,
        sportTypes,

        goBack: () => navigate("/dashboard"),
    };
}
