import { useEffect, useMemo, useState } from "react"
import { useNavigate } from "react-router-dom"
import { useDashboard } from "@/hooks/useDashboard.js"
import useClubs from "@/hooks/useClubs.js"

const DEFAULT_THEME = "dark"
const THEME_STORAGE_KEY = "dashboard_theme"

const EMPTY_CLUB_REQUEST_FORM = {
    name: "",
    city: "",
    sport: "",
    description: "",
}
const EMPTY_AVAILABILITY_FORM = {
    date: "",
    startTime: "",
    endTime: "",
}

function normalizeRequests(dashboardData) {
    return Array.isArray(dashboardData?.pending_requests?.my_requests)
        ? dashboardData.pending_requests.my_requests
        : []
}

function normalizeClubCreationRequests(dashboardData) {
    return Array.isArray(
        dashboardData?.pending_requests?.my_club_creation_requests,
    )
        ? dashboardData.pending_requests.my_club_creation_requests
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

export function useDashboardWorkspace(setUser, texts = {}) {
    const navigate = useNavigate()
    const { dashboardData, loading, error } = useDashboard()
    const {
        clubs: discoverClubs,
        loading: discoverLoading,
        error: discoverError,
    } = useClubs()

    const [activeTab, setActiveTab] = useState("overview")
    const [searchTerm, setSearchTerm] = useState("")
    const [theme, setTheme] = useState(
        () => localStorage.getItem(THEME_STORAGE_KEY) || DEFAULT_THEME,
    )

    const [clubRequestForm, setClubRequestForm] = useState(
        EMPTY_CLUB_REQUEST_FORM,
    )
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

    const myClubs = useMemo(
        () => normalizeClubs(dashboardData),
        [dashboardData],
    )
    const myRequests = useMemo(
        () => normalizeRequests(dashboardData),
        [dashboardData],
    )

    const initialClubCreationRequests = useMemo(
        () => normalizeClubCreationRequests(dashboardData),
        [dashboardData],
    )
    const [clubCreationRequests, setClubCreationRequests] = useState(
        initialClubCreationRequests,
    )

    const myClubIds = useMemo(() => normalizeClubIds(myClubs), [myClubs])
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

    // Persist dashboard-specific theme preference between sessions.
    useEffect(() => {
        localStorage.setItem(THEME_STORAGE_KEY, theme)
    }, [theme])

    // Keep local list in sync when backend payload shape changes.
    useEffect(() => {
        setClubCreationRequests(initialClubCreationRequests)
    }, [initialClubCreationRequests])

    useEffect(() => {
        fetchAvailability()
    }, [])

    function onThemeToggle() {
        setTheme((previousTheme) =>
            previousTheme === "dark" ? "light" : "dark",
        )
    }

    function onGoHome() {
        navigate("/")
    }

    function onSignOut() {
        localStorage.removeItem("currentUser")
        setUser?.(null)
        navigate("/")
    }

    function onClubRequestFieldChange(event) {
        const { name, value } = event.target
        setClubRequestForm((previous) => ({ ...previous, [name]: value }))
    }

    function onAvailabilityFieldChange(event) {
        const { name, value } = event.target
        setAvailabilityForm((previous) => ({ ...previous, [name]: value }))
    }

    function toApiTimestamp(date, time) {
        const localDate = new Date(`${date}T${time}:00`)
        if (Number.isNaN(localDate.getTime())) {
            return ""
        }
        return localDate.toISOString()
    }

    async function fetchAvailability() {
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
    }

    async function onAvailabilitySubmit(event) {
        event.preventDefault()
        setAvailabilityMessage({ type: "", text: "" })

        const { date, startTime, endTime } = availabilityForm
        if (!date || !startTime || !endTime) {
            setAvailabilityMessage({
                type: "error",
                text:
                    texts.fill_all_availability_fields ||
                    "Please fill all availability fields.",
            })
            return
        }

        const startAt = toApiTimestamp(date, startTime)
        const endAt = toApiTimestamp(date, endTime)
        if (!startAt || !endAt) {
            setAvailabilityMessage({
                type: "error",
                text:
                    texts.fill_all_availability_fields ||
                    "Please fill all availability fields.",
            })
            return
        }
        if (new Date(startAt) <= new Date()) {
            setAvailabilityMessage({
                type: "error",
                text:
                    texts.availability_future_only ||
                    "Start time must be in the future.",
            })
            return
        }

        if (new Date(startAt) >= new Date(endAt)) {
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
                body: JSON.stringify({ start_at: startAt, end_at: endAt }),
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
                    [...previous, newBlock].sort((a, b) =>
                        a.start_at.localeCompare(b.start_at),
                    ),
                )
            }
            setAvailabilityForm(EMPTY_AVAILABILITY_FORM)
            setAvailabilityMessage({
                type: "success",
                text: texts.availability_added || "Availability block added.",
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

    async function onClubRequestSubmit(event) {
        event.preventDefault()

        const trimmedName = clubRequestForm.name.trim()
        if (!trimmedName) {
            setClubRequestMessage({
                type: "error",
                text: texts.club_name_required || "Club name is required.",
            })
            return
        }

        setClubRequestSubmitting(true)
        setClubRequestMessage({ type: "", text: "" })

        const payload = {
            name: trimmedName,
            city: clubRequestForm.city.trim(),
            sport: clubRequestForm.sport.trim(),
            description: clubRequestForm.description.trim(),
        }

        try {
            const response = await fetch("/api/me/club-registration-requests", {
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
                        "Could not submit your club request right now.",
                )
            }

            const requestRecord = {
                id: responseBody?.request?.id || `club-request-${Date.now()}`,
                name: responseBody?.request?.name || payload.name,
                city: responseBody?.request?.city || payload.city,
                sport: responseBody?.request?.sport || payload.sport,
                status: responseBody?.request?.status || "pending",
                requested_at:
                    responseBody?.request?.requested_at ||
                    new Date().toISOString(),
            }

            setClubCreationRequests((previous) => [requestRecord, ...previous])
            setClubRequestForm(EMPTY_CLUB_REQUEST_FORM)
            setClubRequestMessage({
                type: "success",
                text: texts.club_request_submitted || "Club request submitted.",
            })
        } catch {
            // Temporary optimistic fallback while backend endpoint is still being merged.
            const fallbackRequest = {
                id: `local-club-request-${Date.now()}`,
                name: payload.name,
                city: payload.city,
                sport: payload.sport,
                status: "pending",
                requested_at: new Date().toISOString(),
            }

            setClubCreationRequests((previous) => [
                fallbackRequest,
                ...previous,
            ])
            setClubRequestForm(EMPTY_CLUB_REQUEST_FORM)
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
        clubCreationRequests,
        clubRequestForm,
        clubRequestSubmitting,
        clubRequestMessage,
        availabilityBlocks,
        availabilityForm,
        availabilityLoading,
        availabilitySubmitting,
        availabilityMessage,
        onThemeToggle,
        onGoHome,
        onSignOut,
        onClubRequestFieldChange,
        onClubRequestSubmit,
        onAvailabilityFieldChange,
        onAvailabilitySubmit,
        onAvailabilityDelete,
    }
}
