import styles from "@/style/Dashboard.module.css";

export const DASHBOARD_TABS = [
    { id: "overview", label: "Overview" },
    { id: "search", label: "Search Clubs" },
    { id: "requests", label: "My Requests" },
    { id: "createClub", label: "Add your own club" },
];

export function statusClass(status) {
    const value = (status || "pending").toLowerCase();
    if (value === "approved") return styles.statusApproved;
    if (value === "rejected") return styles.statusRejected;
    if (value === "cancelled") return styles.statusCancelled;
    return styles.statusPending;
}

export function statusLabel(status) {
    const value = (status || "pending").toLowerCase();
    if (value === "approved") return "Approved";
    if (value === "rejected") return "Rejected";
    if (value === "cancelled") return "Cancelled";
    return "Pending";
}
