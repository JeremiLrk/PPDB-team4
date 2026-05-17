// Match workflow UI component for MatchProposalCard.

import commonStyles from "@/style/common/Common.module.css";
import buttonStyles from "@/style/common/Buttons.module.css";
import styles from "@/style/matches/MatchProposalCard.module.css";
import { statusLabel } from "@/components/dashboard/dashboardUtils.js";
import { useWeather } from "@/hooks/useWeather.js";

function parseDate(value) {
    /*
     Parses a date-like value into a Date object or null.
     Keeps invalid values from leaking into the display formatting helpers.
    */
    if (!value) return null;
    const parsed = new Date(value);
    return Number.isNaN(parsed.getTime()) ? null : parsed;
}

function formatDateTime(value) {
    /*
     Formats a date-like value for display in the proposal card.
    */
    const parsed = parseDate(value);
    if (!parsed) return value || "-";

    return parsed.toLocaleString([], {
        dateStyle: "medium",
        timeStyle: "short",
    });
}

function formatTemplate(template, values = {}) {
    /*
     Replaces template tokens with rendered values.
    */
    return Object.entries(values).reduce(
        (output, [key, value]) => output.replaceAll(`{${key}}`, String(value ?? "")),
        template,
    );
}

function normalizeStatus(status) {
    /*
     Normalizes the proposal status string for style and label lookups.
    */
    return String(status || "pending").toLowerCase();
}

function statusTone(status) {
    /*
     Maps a proposal status to the matching CSS tone class.
    */
    const normalized = normalizeStatus(status);
    if (normalized === "accepted" || normalized === "approved") return styles.statusApproved;
    if (normalized === "rejected") return styles.statusRejected;
    if (normalized === "cancelled" || normalized === "canceled") return styles.statusCancelled;
    if (normalized === "played" || normalized === "finished") return styles.statusFinished;
    return styles.statusPending;
}

function normalizeContact(contact) {
    /*
     Flattens contact data from the various backend shapes into one object.
    */
    if (!contact) return null;

    // Contact objects come from a few backend shapes, so normalize them once here.
    const name = contact.name || [contact.firstName, contact.lastName].filter(Boolean).join(" ").trim();
    const email = contact.email || contact.value || "";
    const phone = contact.phoneNumber || contact.phone || "";

    return {
        id: contact.id || email || name || phone,
        name,
        email,
        phone,
    };
}

function CalendarIcon() {
    /*
     Renders the calendar icon used in the proposal header.
    */
    return (
        <svg viewBox="0 0 24 24" aria-hidden="true">
            <path
                d="M7 2a1 1 0 0 1 1 1v1h8V3a1 1 0 1 1 2 0v1h1.5A2.5 2.5 0 0 1 22 6.5v12A2.5 2.5 0 0 1 19.5 21h-15A2.5 2.5 0 0 1 2 18.5v-12A2.5 2.5 0 0 1 4.5 4H6V3a1 1 0 0 1 1-1Zm12.5 8h-15v8.5c0 .28.22.5.5.5h14a.5.5 0 0 0 .5-.5V10Zm-14-4A.5.5 0 0 0 5 6.5V8h14V6.5a.5.5 0 0 0-.5-.5h-14Z"
                fill="currentColor"
            />
        </svg>
    );
}

function UserIcon() {
    /*
     Renders the user icon for contact rows.
    */
    return (
        <svg viewBox="0 0 24 24" aria-hidden="true">
            <path
                d="M12 12.2a4.1 4.1 0 1 0 0-8.2 4.1 4.1 0 0 0 0 8.2Zm0 2c-3.74 0-7 1.86-7 4.2V21h14v-2.6c0-2.34-3.26-4.2-7-4.2Z"
                fill="currentColor"
            />
        </svg>
    );
}

function MailIcon() {
    /*
     Renders the mail icon for contact rows.
    */
    return (
        <svg viewBox="0 0 24 24" aria-hidden="true">
            <path
                d="M4.5 5.5h15a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2h-15a2 2 0 0 1-2-2v-9a2 2 0 0 1 2-2Zm0 2 7.5 5 7.5-5h-15Zm15 9v-6.18l-6.94 4.63a1 1 0 0 1-1.12 0L4.5 10.32V16.5h15Z"
                fill="currentColor"
            />
        </svg>
    );
}

function PhoneIcon() {
    /*
     Renders the phone icon for contact rows.
    */
    return (
        <svg viewBox="0 0 24 24" aria-hidden="true">
            <path
                d="M7.2 3.5a2.2 2.2 0 0 1 2.06 1.42l1.03 2.73a2.2 2.2 0 0 1-.52 2.31l-1.1 1.1a14.4 14.4 0 0 0 5.33 5.33l1.1-1.1a2.2 2.2 0 0 1 2.31-.52l2.73 1.03a2.2 2.2 0 0 1 1.42 2.06v1.95A2.2 2.2 0 0 1 19.38 22C10.94 22 3.5 14.56 3.5 6.12A2.2 2.2 0 0 1 5.7 3.5H7.2Zm0 2H5.7a.2.2 0 0 0-.2.2c0 7.34 5.96 13.3 13.3 13.3a.2.2 0 0 0 .2-.2v-1.95a.2.2 0 0 0-.13-.19l-2.73-1.03a.2.2 0 0 0-.21.05l-1.44 1.44a1 1 0 0 1-1.1.2 16.4 16.4 0 0 1-7.58-7.58 1 1 0 0 1 .2-1.1l1.44-1.44a.2.2 0 0 0 .05-.21L9.1 5.83a.2.2 0 0 0-.19-.13Z"
                fill="currentColor"
            />
        </svg>
    );
}

function CloudIcon() {
    /*
     Renders the weather icon for the weather strip.
    */
    return (
        <svg viewBox="0 0 24 24" aria-hidden="true">
            <path
                d="M7.7 19h9.7A4.6 4.6 0 1 0 16 10.1 6.4 6.4 0 0 0 3.6 13a4.3 4.3 0 0 0 4.1 6Z"
                fill="currentColor"
            />
        </svg>
    );
}

function ContactBlock({ teamName, contacts, fallbackLabel }) {
    /*
     Renders one team’s contact block with a fallback when no contacts exist.
    */
    const normalizedContacts = (contacts || []).map(normalizeContact).filter(Boolean);

    return (
        <section className={styles.contactBlock}>
            <p className={styles.contactTeam}>{teamName}</p>
            <div className={styles.contactList}>
                {normalizedContacts.length > 0 ? normalizedContacts.map((contact) => (
                    <div className={styles.contactRow} key={contact.id}>
                        {contact.name ? (
                            <div className={styles.contactLine}>
                                <span className={styles.contactIcon}><UserIcon /></span>
                                <span className={styles.contactPrimary}>{contact.name}</span>
                            </div>
                        ) : null}
                        {contact.email ? (
                            <div className={styles.contactLine}>
                                <span className={styles.contactIcon}><MailIcon /></span>
                                <span>{contact.email}</span>
                            </div>
                        ) : null}
                        {contact.phone ? (
                            <div className={styles.contactLine}>
                                <span className={styles.contactIcon}><PhoneIcon /></span>
                                <span>{contact.phone}</span>
                            </div>
                        ) : null}
                    </div>
                )) : (
                    <p className={styles.contactFallback}>{fallbackLabel}</p>
                )}
            </div>
        </section>
    );
}

export default function MatchProposalCard({
    proposal,
    disabled,
    onStatusChange,
    onReportScore,
    reportingMatchId,
    scoreValues,
    onScoreChange,
    onScoreSubmit,
    onCancelScore,
    scoreSubmitting = false,
    canUpdate = true,
    currentUserId,
    texts = {},
    statusTexts = {},
}) {
    /*
     Renders one match proposal card with status, contacts, weather, and score actions.
    */
    const normalizedStatus = normalizeStatus(proposal.status);
    const scoreStatus = String(proposal.scoreStatus || "not_submitted").toLowerCase();
    const scoreSubmissions = Array.isArray(proposal.scoreSubmissions) ? proposal.scoreSubmissions : [];
    const currentUserHasAccepted = Number(proposal.acceptedByUserId) === Number(currentUserId);
    const canRespond = normalizedStatus === "pending" && canUpdate && !currentUserHasAccepted;
    const canCancel = normalizedStatus === "accepted" && canUpdate;
    const canResetPending = normalizedStatus !== "pending" && normalizedStatus !== "played" && canUpdate;
    const currentUserSubmittedScore = scoreSubmissions.some(
        (submission) => Number(submission.submittedBy) === Number(currentUserId),
    );
    const hasScoreSubmission = currentUserSubmittedScore || scoreStatus === "resolved" || scoreStatus === "disputed";
    const canScore = normalizedStatus === "accepted" && typeof onReportScore === "function" && !hasScoreSubmission;
    const displayedStatus = scoreStatus === "resolved"
        ? "finished"
        : proposal.acceptanceStatus === "waiting_for_other"
        ? "waiting_for_other"
        : proposal.status;
    const isReportingScore = reportingMatchId === proposal.id;
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
    const clubNames = Array.from(
        new Set([proposal.team1ClubName, proposal.team2ClubName].filter(Boolean)),
    );
    const clubLabel = clubNames.length > 0 ? clubNames.join(" vs ") : (texts.no_club || "No club");
    const scoreNoticeText = scoreStatus === "resolved"
        ? (texts.score_finalized || "Result confirmed. Elo ratings updated.")
        : scoreStatus === "disputed"
            ? (texts.score_disputed || "Scores do not match. A club manager will decide the decisive score.")
            : (texts.score_waiting || "Score submitted. Waiting for the other team.");

    /*
     The card keeps all proposal state in one place so the list component can stay thin.
    */
    return (
        <li className={styles.card}>
            <div className={styles.iconBox} aria-hidden="true">
                <CalendarIcon />
            </div>

            <div className={styles.content}>
                <div className={styles.headerRow}>
                    <div className={styles.headingBlock}>
                        <p className={styles.title}>
                            {proposal.team1Name} vs {proposal.team2Name}
                        </p>
                        <p className={styles.subtitle}>
                            {proposedDateLabel}: {formatDateTime(proposal.proposedStartAt)} - {formatDateTime(proposal.proposedEndAt)}
                        </p>
                        <p className={styles.clubMeta}>
                            {(texts.club || "Club")}: {clubLabel}
                        </p>
                    </div>

                    <span className={`${styles.statusPill} ${statusTone(displayedStatus)}`}>
                        {/* Show the score state first when the result has already been finalized. */}
                        {displayedStatus === "waiting_for_other"
                            ? (texts.waiting_for_other_player || "Waiting for other player")
                            : displayedStatus === "finished"
                                ? (statusTexts.status_finished || "Finished")
                            : statusLabel(proposal.status, statusTexts)}
                    </span>
                </div>

                <div className={styles.divider} />

                <div className={styles.bodyRow}>
                    <div className={styles.contactsGrid}>
                        <ContactBlock
                            teamName={proposal.team1Name || texts.team_1 || "Team 1"}
                            contacts={proposal.team1Contacts}
                            fallbackLabel={texts.no_contacts || "No contact info"}
                        />
                        <ContactBlock
                            teamName={proposal.team2Name || texts.team_2 || "Team 2"}
                            contacts={proposal.team2Contacts}
                            fallbackLabel={texts.no_contacts || "No contact info"}
                        />
                    </div>

                    <div className={styles.actions}>
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
                            </>
                        ) : null}

                        {canCancel ? (
                            <button
                                className={styles.cancelButton}
                                type="button"
                                disabled={disabled}
                                onClick={() => onStatusChange(proposal.id, "cancelled")}
                            >
                                {texts.cancel || "Cancel"}
                            </button>
                        ) : null}

                        {canScore ? (
                            <button
                                className={buttonStyles.primaryButton}
                                type="button"
                                disabled={disabled}
                                onClick={() => onReportScore(proposal.id)}
                            >
                                {texts.report_score || "Add Score"}
                            </button>
                        ) : null}

                        {canResetPending ? (
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
                </div>

                {isReportingScore ? (
                    <form className={styles.inlineScoreForm} onSubmit={(event) => onScoreSubmit(event, proposal.id)}>
                        {/* The decisive score form only appears for disputed or unresolved matches. */}
                        <h4 className={styles.inlineScoreTitle}>
                            {texts.adjudicate_title || "Submit decisive score"}
                        </h4>
                        <div className={styles.inlineScoreInputs}>
                            <input
                                className={styles.inlineScoreInput}
                                type="number"
                                min="0"
                                value={scoreValues.team1}
                                onChange={(event) => onScoreChange("team1", event.target.value)}
                                placeholder="0"
                                required
                            />
                            <span className={styles.inlineScoreSeparator}>-</span>
                            <input
                                className={styles.inlineScoreInput}
                                type="number"
                                min="0"
                                value={scoreValues.team2}
                                onChange={(event) => onScoreChange("team2", event.target.value)}
                                placeholder="0"
                                required
                            />
                            <button
                                className={buttonStyles.primaryButton}
                                type="submit"
                                disabled={scoreSubmitting}
                            >
                                {scoreSubmitting ? "..." : (texts.confirm || "Submit")}
                            </button>
                            <button
                                className={buttonStyles.secondaryButton}
                                type="button"
                                onClick={onCancelScore}
                            >
                                {texts.cancel || "Cancel"}
                            </button>
                        </div>
                    </form>
                ) : null}

                {hasScoreSubmission ? (
                    <div className={`${styles.scoreNotice} ${scoreStatus === "resolved" ? styles.scoreNoticeFinalized : styles.scoreNoticePending}`}>
                        {/* This notice explains whether the result is waiting, disputed, or finalized. */}
                        {scoreNoticeText}
                    </div>
                ) : null}

                {weatherClubId ? (
                    <p className={styles.weatherLine}>
                        <span className={styles.weatherIcon}><CloudIcon /></span>
                        {weatherLoading
                            ? weatherLoadingText
                            : weatherTemp !== null
                                ? weatherAvailableText
                                : weatherUnavailableText}
                    </p>
                ) : null}
            </div>
        </li>
    );
}
