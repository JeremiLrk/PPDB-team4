import styles from "@/style/common/Common.module.css";

export function getDashboardTabs(texts) {
    return [
        { id: "overview", label: texts.tab_overview || "Overview" },
        { id: "profile", label: texts.tab_profile || "My Profile" },
        { id: "availability", label: texts.tab_availability || "Availability" },
        { id: "search", label: texts.tab_search || "Search Clubs" },
        { id: "requests", label: texts.tab_requests || "My Requests" },
        { id: "teams",      label: texts.tab_teams       || "My Teams" },
        { id: "matches", label: texts.tab_matches || "Matches" },
        { id: "createClub", label: texts.tab_create_club || "Add your own club" },
        { id: "manageClubs", label: texts.tab_manage_club || "Manage your clubs"},
    ]
}

export function statusClass(status) {
    const value = (status || "pending").toLowerCase()
    if (value === "approved") return styles.statusApproved
    if (value === "rejected") return styles.statusRejected
    if (value === "cancelled") return styles.statusCancelled
    return styles.statusPending
}

export function statusLabel(status, texts = {}) {
    const value = (status || "pending").toLowerCase()
    if (value === "approved") return texts.status_approved || "Approved"
    if (value === "rejected") return texts.status_rejected || "Rejected"
    if (value === "cancelled") return texts.status_cancelled || "Cancelled"
    return texts.status_pending || "Pending"
}
