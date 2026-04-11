import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";

export function useClubSettings(clubId) {
    const navigate = useNavigate();

    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [activeTab, setActiveTab] = useState("overview");

    const [club, setClub] = useState(null);
    const [formData, setFormData] = useState({
        name: "",
        description: "",
        city: "",
        sport: "",
    });

    const [members, setMembers] = useState([]);
    const [ladders, setLadders] = useState([]);

    const [ratingFunctions, setRatingFunctions] = useState([]);
    const [ruleSets, setRuleSets] = useState([]);

    const [updating, setUpdating] = useState(false);
    const [updateMessage, setUpdateMessage] = useState(null);

    useEffect(() => {
        async function fetchClubData() {
            try {
                // Fetching core data + the metadata for dropdowns
                const [clubRes, membersRes, laddersRes, ratingsRes, rulesRes] = await Promise.all([
                    fetch(`/api/clubs/${clubId}`, { credentials: "include" }),
                    fetch(`/api/clubs/${clubId}/members`, { credentials: "include" }),
                    fetch(`/api/clubs/${clubId}/ladders`, { credentials: "include" }),
                    fetch(`/api/rating-functions`), 
                    fetch(`/api/rule-sets`)
                ]);

                const clubData = await clubRes.json();
                const membersData = await membersRes.json();
                const laddersData = await laddersRes.json();
                const ratingsData = await ratingsRes.json();
                const rulesData = await rulesRes.json();

                if (!clubRes.ok) throw new Error(clubData.message);

                setClub(clubData.club);
                setFormData({
                    name: clubData.club.name || "",
                    description: clubData.club.description || "",
                    city: clubData.club.city || "",
                    sport: clubData.club.sport || "",
                });

                setMembers(membersData.members || []);
                
                // Handle the array response from your Flask API
                setLadders(Array.isArray(laddersData) ? laddersData : (laddersData.ladders || []));

                // Set dropdown options
                setRatingFunctions(ratingsData.ratingFunctions || []);
                setRuleSets(rulesData.ruleSets || []);

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
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(formData),
            });

            const data = await res.json();

            if (!res.ok) throw new Error(data.message);

            setClub(prev => ({ ...prev, ...formData }));

            setUpdateMessage({ type: "success", text: "Saved successfully" });

        } catch (err) {
            setUpdateMessage({ type: "error", text: err.message });
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
            setError(err.message);
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
            setError(err.message);
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
            setError(err.message);
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

        ladders,
        createLadder,

        ratingFunctions,
        ruleSets,

        goBack: () => navigate("/dashboard"),
    };
}