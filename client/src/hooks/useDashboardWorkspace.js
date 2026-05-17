// Shared hook for useDashboardWorkspace.

import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useDashboard } from "@/hooks/useDashboard.js";
import useClubs from "@/hooks/useClubs.js";
import { notify } from "@/hooks/useNotify.js";
import { useCurrentUserContext } from "@/context/useCurrentUserContext";
import { useTeams } from "@/hooks/teams/useTeams.js";
import { useSportTypes } from "@/hooks/useSportTypes.js"

const DEFAULT_THEME = "dark"
const THEME_STORAGE_KEY = "dashboard_theme"

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
    /*
     Flattens the nested join-request list from the dashboard payload.
    */
    return Array.isArray(dashboardData?.pending_requests?.my_requests)
        ? dashboardData.pending_requests.my_requests
        : []
}

function normalizeClubs(dashboardData) {
    /*
     Normalizes the dashboard club list into a safe array.
    */
    return Array.isArray(dashboardData?.clubs) ? dashboardData.clubs : []
}

function normalizeClubIds(clubs) {
    /*
     Builds a numeric set of club identifiers from the dashboard club list.
     This is used for fast membership checks when the workspace needs to know
     whether the current user already belongs to a given club.
    */
    return new Set(
        clubs
            .map((club) => Number(club?.id ?? club?.club_id))
            .filter((clubId) => Number.isFinite(clubId)),
    )
}

function normalizeUpcomingMatches(dashboardData) {
    /*
     Normalizes the upcoming match list into a safe array.
    */
    return Array.isArray(dashboardData?.upcoming_matches)
        ? dashboardData.upcoming_matches
        : []
}

function normalizePendingJoinRequestClubIds(myRequests) {
    /*
     Collects club IDs that already have a pending join request.
    */
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
    /*
     Owns dashboard state and the handlers the pages reuse.
    */
    const navigate = useNavigate();
    const { dashboardData, loading, error } = useDashboard();
    const { setCurrentUser } = useCurrentUserContext();
    const { sportTypes } = useSportTypes();
    const {
        clubs: discoverClubs,
        loading: discoverLoading,
        error: discoverError,
    } = useClubs()
    /*
     Owns the dashboard workspace state for tabs, forms, and filters.
    */

    const [activeTab, setActiveTab] = useState("overview")
    const [searchTerm, setSearchTerm] = useState("")
    const [theme, setTheme] = useState(
        () => localStorage.getItem(THEME_STORAGE_KEY) || DEFAULT_THEME,
    )

    const [clubRequestForm, setClubRequestForm] = useState(
        EMPTY_CLUB_REQUEST_FORM,
    )
    const [clubRequestCitySelection, setClubRequestCitySelection] = useState(null)
    const [clubRequestSubmitting, setClubRequestSubmitting] = useState(false)
    const [clubRequestMessage, setClubRequestMessage] = useState({
        type: "",
        text: "",
    })
    // Availability blocks drive the weekly calendar shown in the dashboard tab.
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
        // Filter the already loaded list instead of refetching on every keystroke.
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

    useEffect(() => {
        localStorage.setItem(THEME_STORAGE_KEY, theme)
    }, [theme])

    function onThemeToggle() {
        /*
         Toggles the dashboard theme without touching loaded data.
        */
        setTheme((previousTheme) =>
            previousTheme === "dark" ? "light" : "dark",
        )
    }

    function onGoHome() {
        /*
         Navigates back to the public landing page.
         The handler does not clear dashboard state because the app can keep the
         session data warm if the user comes back immediately.
        */
        navigate("/")
    }

    function onGoSettings(ClubId) {
        /*
         Opens the settings page for one club.
         The caller already knows which club should be configured, so this only
         needs to translate that id into the expected route.
        */
        navigate(`/clubs/${ClubId}/settings`)
    }
    async function onSignOut() {
        /*
         Clears local session state and then signs out through the API.
        */
        /*
         Clears local session state and then closes the server session.
        */
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
        /*
         Updates one club-request field and resets the city pick when needed.
        */
        const { name, value } = event.target
        setClubRequestForm((previous) => ({ ...previous, [name]: value }))
        if (name === "city") {
            // Changing the typed city clears the previously picked suggestion.
            setClubRequestCitySelection(null)
        }
    }

    function onClubRequestCitySelect(city) {
        /*
         Copies the selected city suggestion into the form state.
        */
        setClubRequestForm((previous) => ({ ...previous, city: city.label }))
        setClubRequestCitySelection(city)
    }

    function onAvailabilityFieldChange(event) {
        /*
         Mirrors the availability inputs into local state.
        */
        const { name, value } = event.target
        setAvailabilityForm((previous) => ({ ...previous, [name]: value }))
    }

    const fetchAvailability = useCallback(async () => {
        /*
         Loads the current availability blocks from the backend.
        */
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
            // Keep the raw availability rows and let the tab handle formatting.
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
        /*
         Loads availability once when the dashboard workspace mounts.
        */
        fetchAvailability()
    }, [fetchAvailability])

    async function onAvailabilitySubmit(event) {
        /*
         Validates and submits one new availability block.
        */
        event.preventDefault()
        setAvailabilityMessage({ type: "", text: "" })

        const { weekday, startTime, endTime } = availabilityForm
        if (weekday === "" || !startTime || !endTime) {
            // All three fields are required before we can submit a block.
            setAvailabilityMessage({
                type: "error",
                text:
                    texts.fill_all_availability_fields ||
                    "Please fill all availability fields.",
            })
            return
        }

        if (startTime >= endTime) {
            // Keep blocks strictly ordered so the weekly calendar stays valid.
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
                // Resort after insert so the weekly strip remains in calendar order.
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
        /*
         Deletes one availability block and updates the local list.
        */
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

            // Removing the block locally keeps the view in sync without a reload.
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
        /*
         Creates a join request for the selected club.
        */
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
        /*
         Approves or rejects one incoming club join request.
        */
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
        /*
         Loads incoming join requests and checks owner access.
        */
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
            // A 200 means the current user has owner access for this club view.
            setIsClubOwner(true);
        } else {
            setIsClubOwner(false);
        }
        return await res.json();
    }
    const [incomingJoinRequests, setIncomingJoinRequests] = useState([]);

    useEffect(() => {
        /*
         Loads the owner-only join requests on mount.
        */
        fetchJoinRequests()
            .then(data => {
                setIncomingJoinRequests(data.requests || []);
            })
            .catch(err => console.error("Not an owner or fetch failed", err));
    }, []);

    async function onClubRequestSubmit(event) {
        /*
         Submits the club-request form after basic validation.
        */
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
            // The club-request payload is already normalized above, so the POST can stay simple here.
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

            // Success resets the form and clears the selected city suggestion.
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
        onThemeToggle,
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
