import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useDashboard } from "@/hooks/useDashboard.js";
import useClubs from "@/hooks/useClubs.js";
import { notify } from "@/hooks/useNotify.js";
import { useCurrentUserContext } from "@/context/useCurrentUserContext";
import { useTeams } from "@/hooks/teams/useTeams.js";
import { useSportTypes } from "@/hooks/useSportTypes.js"
import { useThemeContext } from "@/context/useThemeContext.jsx"

const EMPTY_CLUB_REQUEST_FORM = {
    name: "",
    city: "",
    sport_type_id: "",
    description: "",
}
const EMPTY_AVAILABILITY_FORM = {
    weekday: "",
    startTime: "",
    endTime: "",
}

const WEEKDAY_OPTIONS_EN = [
    { value: "0", label: "Monday" },
    { value: "1", label: "Tuesday" },
    { value: "2", label: "Wednesday" },
    { value: "3", label: "Thursday" },
    { value: "4", label: "Friday" },
    { value: "5", label: "Saturday" },
    { value: "6", label: "Sunday" },
]

const WEEKDAY_OPTIONS_NL = [
    { value: "0", label: "Maandag" },
    { value: "1", label: "Dinsdag" },
    { value: "2", label: "Woensdag" },
    { value: "3", label: "Donderdag" },
    { value: "4", label: "Vrijdag" },
    { value: "5", label: "Zaterdag" },
    { value: "6", label: "Zondag" },
]

function normalizeRequests(dashboardData) {
    return Array.isArray(dashboardData?.pending_requests?.my_requests)
        ? dashboardData.pending_requests.my_requests
        : []
}

function normalizeClubs(dashboardData) {
    return Array.isArray(dashboardData?.clubs) ? dashboardData.clubs : []
}

function normalizeClubIds(clubs) {
    return new Set(
        clubs
            .map((club) => Number(club?.id ?? club?.club_id))
            .filter((clubId) => Number.isFinite(clubId)),
    )
}

function normalizeUpcomingMatches(dashboardData) {
    return Array.isArray(dashboardData?.upcoming_matches)
        ? dashboardData.upcoming_matches
        : []
}

function normalizePendingJoinRequestClubIds(myRequests) {
    return new Set(
        myRequests
            .filter(
                (request) =>
                    (request?.status || "pending").toLowerCase() === "pending",
            )
            .map((request) => Number(request?.club_id ?? request?.club?.id))
            .filter((clubId) => Number.isFinite(clubId)),
    )
}

export function useDashboardWorkspace(setUser, texts = {}, lang = "en") {
    const navigate = useNavigate();
    const { dashboardData, loading, error } = useDashboard();
    const { setCurrentUser } = useCurrentUserContext();
    const { sportTypes } = useSportTypes();
    const { theme, toggleTheme } = useThemeContext();
    const {
        clubs: discoverClubs,
        loading: discoverLoading,
        error: discoverError,
    } = useClubs()

    const [activeTab, setActiveTab] = useState("overview")
    const [searchTerm, setSearchTerm] = useState("")

    const [clubRequestForm, setClubRequestForm] = useState(
        EMPTY_CLUB_REQUEST_FORM,
    )
    const [clubRequestCitySelection, setClubRequestCitySelection] = useState(null)
    const [clubRequestSubmitting, setClubRequestSubmitting] = useState(false)
    const [clubRequestMessage, setClubRequestMessage] = useState({
        type: "",
        text: "",
    })
    const [availabilityBlocks, setAvailabilityBlocks] = useState([])
    const [availabilityForm, setAvailabilityForm] = useState(
        EMPTY_AVAILABILITY_FORM,
    )
    const [availabilityLoading, setAvailabilityLoading] = useState(true)
    const [availabilitySubmitting, setAvailabilitySubmitting] = useState(false)
    const [availabilityMessage, setAvailabilityMessage] = useState({
        type: "",
        text: "",
    })

    const [isClubOwner, setIsClubOwner] = useState(false);
    const weekdayOptions = useMemo(
        () => (String(lang).toLowerCase().startsWith("nl") ? WEEKDAY_OPTIONS_NL : WEEKDAY_OPTIONS_EN),
        [lang],
    )

    const myClubs = useMemo(() => normalizeClubs(dashboardData), [dashboardData]);
    const myRequests = useMemo(() => normalizeRequests(dashboardData), [dashboardData]);

    const myClubIds = useMemo(() => normalizeClubIds(myClubs), [myClubs])
    const upcomingMatches = useMemo(
        () => normalizeUpcomingMatches(dashboardData),
        [dashboardData],
    )
    const pendingJoinRequestClubIds = useMemo(
        () => normalizePendingJoinRequestClubIds(myRequests),
        [myRequests],
    )

    const filteredDiscoverClubs = useMemo(() => {
        const term = searchTerm.trim().toLowerCase()
        if (!term) return discoverClubs
        return discoverClubs.filter((club) =>
            (club?.name || "").toLowerCase().includes(term),
        )
    }, [discoverClubs, searchTerm])

    // My teams (managed by current account)
    const {
        teams: myTeams,
        total: myTeamsTotal,
        loading: myTeamsLoading,
        error: myTeamsError,
        sort: myTeamsSort,
        pageSize: myTeamsPageSize,
        hasMore: myTeamsHasMore,
        load: loadMyTeams,
        loadMore: loadMoreMyTeams,
    } = useTeams({ pageSize: 12, sort: "name", endpoint: "/api/teams/my-all" });

    // Persist dashboard-specific theme preference between sessions.
    function onGoHome() {
        navigate("/")
    }

    function onGoSettings(ClubId) {
        navigate(`/clubs/${ClubId}/settings`)
    }

    async function onSignOut() {
        localStorage.removeItem("currentUser");
        setUser?.(null);
        navigate("/");
        try {
            const response = await fetch("/api/logout", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                credentials: "include",
            });

            const data = await response.json();
            if (!response.ok) {
                throw new Error(data?.message || "Uitloggen mislukt");
            }

            setCurrentUser(null);
            notify.success("Uitloggen gelukt");
            navigate("/");
        } catch (err) {
            console.error(err?.message || "Uitloggen mislukt");
            notify.error(err?.message || "Uitloggen mislukt");
        }
    }

    function onClubRequestFieldChange(event) {
        const { name, value } = event.target
        setClubRequestForm((previous) => ({ ...previous, [name]: value }))
        if (name === "city") {
            setClubRequestCitySelection(null)
        }
    }

    function onClubRequestCitySelect(city) {
        setClubRequestForm((previous) => ({ ...previous, city: city.label }))
        setClubRequestCitySelection(city)
    }

    function onAvailabilityFieldChange(event) {
        const { name, value } = event.target
        setAvailabilityForm((previous) => ({ ...previous, [name]: value }))
    }

    const fetchAvailability = useCallback(async () => {
        setAvailabilityLoading(true)
        try {
            const response = await fetch("/api/me/availability", {
                method: "GET",
                credentials: "include",
            })

            let body = {}
            try {
                body = await response.json()
            } catch {
                body = {}
            }

            if (!response.ok) {
                throw new Error(
                    body?.message ||
                        texts.could_not_load_availability ||
                        "Could not load availability.",
                )
            }

            const blocks = Array.isArray(body?.availability)
                ? body.availability
                : []
            setAvailabilityBlocks(blocks)
        } catch (error) {
            setAvailabilityMessage({
                type: "error",
                text:
                    error?.message ||
                    texts.could_not_load_availability ||
                    "Could not load availability.",
            })
        } finally {
            setAvailabilityLoading(false)
        }
    }, [texts.could_not_load_availability])

    useEffect(() => {
        fetchAvailability()
    }, [fetchAvailability])

    async function onAvailabilitySubmit(event) {
        event.preventDefault()
        setAvailabilityMessage({ type: "", text: "" })

        const { weekday, startTime, endTime } = availabilityForm
        if (weekday === "" || !startTime || !endTime) {
            setAvailabilityMessage({
                type: "error",
                text:
                    texts.fill_all_availability_fields ||
                    "Please fill all availability fields.",
            })
            return
        }

        if (startTime >= endTime) {
            setAvailabilityMessage({
                type: "error",
                text:
                    texts.availability_start_before_end ||
                    "Start time must be before end time.",
            })
            return
        }

        setAvailabilitySubmitting(true)
        try {
            const response = await fetch("/api/me/availability", {
                method: "POST",
                credentials: "include",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    weekday: Number(weekday),
                    start_time: startTime,
                    end_time: endTime,
                }),
            })

            let body = {}
            try {
                body = await response.json()
            } catch {
                body = {}
            }

            if (!response.ok) {
                throw new Error(
                    body?.message ||
                        texts.could_not_add_availability ||
                        "Could not add availability.",
                )
            }

            const newBlock = body?.block
            if (newBlock?.id) {
                setAvailabilityBlocks((previous) =>
                    [...previous, newBlock].sort((a, b) => {
                        const weekdayDiff = Number(a.weekday) - Number(b.weekday)
                        if (weekdayDiff !== 0) {
                            return weekdayDiff
                        }
                        return String(a.start_time).localeCompare(String(b.start_time))
                    }),
                )
            }
            setAvailabilityForm(EMPTY_AVAILABILITY_FORM)
            setAvailabilityMessage({
                type: "success",
                text: texts.availability_added || "Availability saved.",
            })
        } catch (error) {
            setAvailabilityMessage({
                type: "error",
                text:
                    error?.message ||
                    texts.could_not_add_availability ||
                    "Could not add availability.",
            })
        } finally {
            setAvailabilitySubmitting(false)
        }
    }

    async function onAvailabilityDelete(blockId) {
        setAvailabilityMessage({ type: "", text: "" })
        try {
            const response = await fetch(`/api/me/availability/${blockId}`, {
                method: "DELETE",
                credentials: "include",
            })

            let body = {}
            try {
                body = await response.json()
            } catch {
                body = {}
            }

            if (!response.ok) {
                throw new Error(
                    body?.message ||
                        texts.could_not_delete_availability ||
                        "Could not delete availability.",
                )
            }

            setAvailabilityBlocks((previous) =>
                previous.filter((block) => block.id !== blockId),
            )
            setAvailabilityMessage({
                type: "success",
                text:
                    texts.availability_deleted || "Availability block deleted.",
            })
        } catch (error) {
            setAvailabilityMessage({
                type: "error",
                text:
                    error?.message ||
                    texts.could_not_delete_availability ||
                    "Could not delete availability.",
            })
        }
    }
    async function clubJoinrequest(clubId) {
        const res = await fetch("/api/club/join-request", {
            method: "POST",
            credentials: "include",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ club_id: clubId })
        });

        if (!res.ok) {
            throw new Error("Request failed");
        }
    }
    async function decideJoinrequest(clubId, userId, status) {
        const res = await fetch("/api/club/join-request/decide", {
            method: "POST",
            credentials: "include",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ 
                club_id: clubId,
                user_id: userId,
                status: status
            })
        });

        if (!res.ok) {
            throw new Error("Request failed");
        }
    }
    async function fetchJoinRequests() {
        const res = await fetch("/api/club/join-request", {
            method: "GET",
            credentials: "include",
            headers: {
                "Content-Type": "application/json"
            }
        });

        if (!res.ok) {
            throw new Error("Failed to fetch join requests");
        }
        if (res.status === 200) {
            setIsClubOwner(true);
        } else {
            setIsClubOwner(false);
        }
        return await res.json();
    }
    const [incomingJoinRequests, setIncomingJoinRequests] = useState([]);

    useEffect(() => {
        fetchJoinRequests()
            .then(data => {
                setIncomingJoinRequests(data.requests || []);
            })
            .catch(err => console.error("Not an owner or fetch failed", err));
    }, []);

    async function onClubRequestSubmit(event) {
        event.preventDefault()

        const trimmedName = clubRequestForm.name.trim()
        const selectedCity = clubRequestCitySelection?.label?.trim()
        if (!trimmedName) {
            setClubRequestMessage({
                type: "error",
                text: texts.club_name_required || "Club name is required.",
            })
            return
        }

        if (!selectedCity) {
            setClubRequestMessage({
                type: "error",
                text: texts.city_selection_required || "Please choose a real city from the suggestions.",
            })
            return
        }

        setClubRequestSubmitting(true)
        setClubRequestMessage({ type: "", text: "" })

        const payload = {
            name: trimmedName,
            city: selectedCity,
            sport_type_id: clubRequestForm.sport_type_id.trim(),
            description: clubRequestForm.description.trim(),
        }

        try {
            const response = await fetch("/api/clubs", {
                method: "POST",
                credentials: "include",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            })

            let responseBody = {}
            try {
                responseBody = await response.json()
            } catch {
                responseBody = {}
            }

            if (!response.ok) {
                throw new Error(
                    responseBody?.message ||
                    texts.could_not_submit_club_request ||
                    "Could not submit your club request right now."
                );
            }

            setClubRequestForm(EMPTY_CLUB_REQUEST_FORM)
            setClubRequestCitySelection(null)
            setClubRequestMessage({
                type: "success",
                text: texts.club_request_submitted || "Club request submitted.",
            })
        } catch (error) {
            setClubRequestMessage({
                type: "error",
                text:
                    error?.message ||
                    texts.could_not_submit_club_request ||
                    "Could not submit your club request right now.",
            })
        } finally {
            setClubRequestSubmitting(false)
        }
    }

    return {
        loading,
        error,
        theme,
        activeTab,
        setActiveTab,
        searchTerm,
        setSearchTerm,
        myClubs,
        myRequests,
        myClubIds,
        pendingJoinRequestClubIds,
        filteredDiscoverClubs,
        discoverLoading,
        discoverError,
        clubRequestForm,
        clubRequestCitySelection,
        clubRequestSubmitting,
        clubRequestMessage,
        incomingJoinRequests,
        isClubOwner,
        onGoSettings,
        decideJoinrequest,
        clubJoinrequest,
        onClubRequestFieldChange,
        onClubRequestCitySelect,
        availabilityBlocks,
        upcomingMatches,
        availabilityForm,
        availabilityLoading,
        availabilitySubmitting,
        availabilityMessage,
        onThemeToggle: toggleTheme,
        onGoHome,
        onSignOut,
        onClubRequestSubmit,
        myTeams,
        myTeamsTotal,
        myTeamsLoading,
        myTeamsError,
        myTeamsSort,
        myTeamsPageSize,
        myTeamsHasMore,
        loadMyTeams,
        loadMoreMyTeams,
        onAvailabilityFieldChange,
        onAvailabilitySubmit,
        onAvailabilityDelete,
        sportTypes,
        weekdayOptions,
    };
}
