import commonStyles from "@/style/common/Common.module.css";
import styles from "@/style/matches/MatchProposalCard.module.css";
import ItemCard from "@/components/common/ItemCard.jsx";
import { statusLabel } from "@/components/dashboard/dashboardUtils.js";
import { useWeather } from "@/hooks/useWeather.js";

function parseDate(value) {
    if (!value) return null;
    const parsed = new Date(value);
    return Number.isNaN(parsed.getTime()) ? null : parsed;
}

function formatDateTime(value) {
    const parsed = parseDate(value);
    if (!parsed) return value || "-";

    return parsed.toLocaleString([], {
        dateStyle: "medium",
        timeStyle: "short",
    });
}

function formatTemplate(template, values = {}) {
    return Object.entries(values).reduce(
        (output, [key, value]) => output.replaceAll(`{${key}}`, String(value ?? "")),
        template,
    );
}

function statusClass(status) {
    const normalized = (status || "pending").toLowerCase();
    if (normalized === "accepted" || normalized === "approved") {
        return commonStyles.statusApproved;
    }
    if (normalized === "rejected") {
        return commonStyles.statusRejected;
    }
    if (normalized === "cancelled" || normalized === "canceled") {
        return commonStyles.statusCancelled;
    }
    return commonStyles.statusPending;
}

function formatContact(contact) {
    if (!contact) return "";
    const name = contact.name || [contact.firstName, contact.lastName].filter(Boolean).join(" ").trim();
    const email = contact.email || contact.value || "";

    if (name && email && name !== email) {
        return `${name} <${email}>`;
    }

    return name || email || "";
}

function formatContactList(contacts = []) {
    return contacts
        .map(formatContact)
        .filter(Boolean)
        .join(", ");
}

export default function MatchProposalCard({ proposal, disabled, onStatusChange, texts = {}, statusTexts = {} }) {
    const normalizedStatus = (proposal.status || "pending").toLowerCase();
    const canRespond = normalizedStatus === "pending";
    const canResetToPending = normalizedStatus !== "pending";
    const weatherClubId = proposal.team1ClubId || proposal.team2ClubId || null;
    const weatherCity = proposal.team1ClubCity || proposal.team2ClubCity || "";
    const weatherDate = formatDateTime(proposal.proposedStartAt);
    const { weather, loading: weatherLoading } = useWeather(weatherClubId, proposal.proposedStartAt);
    const weatherDescription = weather?.weather?.[0]?.description || "";
    const weatherTemp = Number.isFinite(weather?.main?.temp) ? Math.round(weather.main.temp) : null;
    const weatherLocation = weatherCity || weather?.name || texts.club || "club";
    const proposedDateLabel = texts.proposed_date || "Proposed date";
    const weatherLoadingLabel = texts.weather_loading || "Weather for {city} on {date} loading...";
    const weatherAvailableLabel = texts.weather_available || "Weather for {city} on {date}: {temp}°C{description}";
    const weatherUnavailableLabel = texts.weather_unavailable || "Weather for {city} on {date} unavailable";
    const weatherLoadingText = formatTemplate(weatherLoadingLabel, { city: weatherLocation, date: weatherDate });
    const weatherAvailableText = formatTemplate(weatherAvailableLabel, {
        city: weatherLocation,
        date: weatherDate,
        temp: weatherTemp ?? "-",
        description: weatherDescription ? `, ${weatherDescription}` : "",
    });
    const weatherUnavailableText = formatTemplate(weatherUnavailableLabel, {
        city: weatherLocation,
        date: weatherDate,
    });

    return (
        <ItemCard>
            <div>
                <p className={commonStyles.primaryText}>
                    {proposal.team1Name} vs {proposal.team2Name}
                </p>
                <p className={commonStyles.secondaryText}>
                    {proposedDateLabel}: {formatDateTime(proposal.proposedStartAt)} - {formatDateTime(proposal.proposedEndAt)}
                </p>
                {(proposal.team1Contacts?.length || proposal.team2Contacts?.length) ? (
                    <div className={commonStyles.secondaryText} style={{ display: "grid", gap: "0.2rem" }}>
                        <p style={{ margin: 0 }}>
                            {proposal.team1Name || texts.team1 || "Team 1"}: {formatContactList(proposal.team1Contacts)}
                        </p>
                        <p style={{ margin: 0 }}>
                            {proposal.team2Name || texts.team2 || "Team 2"}: {formatContactList(proposal.team2Contacts)}
                        </p>
                    </div>
                ) : null}
                {weatherClubId ? (
                    <p className={commonStyles.secondaryText}>
                        {weatherLoading
                            ? weatherLoadingText
                            : weatherTemp !== null
                                ? weatherAvailableText
                                : weatherUnavailableText}
                    </p>
                ) : null}
            </div>

            <div
                className={styles.actionRow}
            >
                <span className={`${commonStyles.statusPill} ${statusClass(proposal.status)}`}>
                    {statusLabel(proposal.status, statusTexts)}
                </span>

                {canRespond ? (
                    <>
                        <button
                            className={styles.acceptButton}
                            type="button"
                            disabled={disabled}
                            onClick={() => onStatusChange(proposal.id, "accepted")}
                        >
                            {texts.accept || "Accept"}
                        </button>
                        <button
                            className={styles.rejectButton}
                            type="button"
                            disabled={disabled}
                            onClick={() => onStatusChange(proposal.id, "rejected")}
                        >
                            {texts.reject || "Reject"}
                        </button>
                        <button
                            className={styles.cancelButton}
                            type="button"
                            disabled={disabled}
                            onClick={() => onStatusChange(proposal.id, "cancelled")}
                        >
                            {texts.cancel || "Cancel"}
                        </button>
                    </>
                ) : null}

                {canResetToPending ? (
                    <button
                        className={styles.resetButton}
                        type="button"
                        disabled={disabled}
                        onClick={() => onStatusChange(proposal.id, "pending")}
                    >
                        {texts.reset_pending || "Set back to pending"}
                    </button>
                ) : null}
            </div>
        </ItemCard>
    );
}
