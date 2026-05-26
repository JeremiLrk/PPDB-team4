// Dashboard UI component for DashboardTabs.

import { useEffect, useState } from "react";
import { Link} from "react-router-dom";
import formStyles from "@/style/common/Forms.module.css";
import commonStyles from "@/style/common/Common.module.css";
import dashStyles from "@/style/ClubSettings.module.css";

import {statusClass, statusLabel} from "@/components/dashboard/dashboardUtils.js";
import { GENDER_SELECT_OPTIONS, GENDER_VALUES } from "@/constants/genderOptions.js";
import CityAutocompleteField from "@/components/common/CityAutocompleteField.jsx";
import { useThemeContext } from "@/context/useThemeContext.jsx";

const GENDER_TEXT_KEYS = {
    male: "gender_male",
    female: "gender_female",
    other: "gender_other",
}

function profileGenderFromUser(user) {
    /*
     Converts the stored gender value into the select-friendly form value.
    */
    const g = user?.gender
    return GENDER_VALUES.includes(g) ? g : ""
}

function parseUtcTimestamp(value) {
    /*
     Parses an API timestamp into a Date or null.
    */
    if (typeof value !== "string") {
        return null
    }

    const parsed = new Date(value)

    if (Number.isNaN(parsed.getTime())) {
        return null
    }

    return parsed
}

function formatLocalTimestamp(value, locale = "en-US") {
    /*
     Formats an API timestamp in the current locale.
    */
    const parsed = parseUtcTimestamp(value)
    if (!parsed) {
        return value || "-"
    }

    return parsed.toLocaleString(locale)
}

function formatLocalDate(value, locale = "en-US") {
    /*
     Formats an API date or timestamp as a date-only label.
    */
    const parsed = parseUtcTimestamp(value)
    if (!parsed) {
        return value || "-"
    }

    return parsed.toLocaleDateString(locale, {
        year: "numeric",
        month: "short",
        day: "numeric",
    })
}

const EN_WEEKDAY_LABELS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]

const NL_WEEKDAY_LABELS = [
    "Maandag",
    "Dinsdag",
    "Woensdag",
    "Donderdag",
    "Vrijdag",
    "Zaterdag",
    "Zondag",
]

function isDutchLang(lang) {
    /*
     Checks whether the active language should use Dutch labels.
    */
    return (lang || "").toLowerCase().startsWith("nl")
}

function defaultText(lang, english, dutch) {
    /*
     Returns the language-specific fallback text.
    */
    return isDutchLang(lang) ? dutch : english
}

function formatWeeklyAvailability(block, lang) {
    /*
     Formats one weekly availability block for display.
    */
    const weekdayIndex = Number(block?.weekday)
    const weekdayLabels = isDutchLang(lang) ? NL_WEEKDAY_LABELS : EN_WEEKDAY_LABELS
    const weekdayLabel = weekdayLabels[weekdayIndex] || block?.weekday_label || defaultText(lang, "Day", "Dag")
    const startTime = block?.start_time || "--:--"
    const endTime = block?.end_time || "--:--"

    if (block?.weekday !== undefined && block?.weekday !== null) {
        return `${weekdayLabel} ${startTime} - ${endTime}`
    }

    if (block?.start_at && block?.end_at) {
        const locale = isDutchLang(lang) ? "nl-BE" : "en-US"
        return `${formatLocalTimestamp(block.start_at, locale)} - ${formatLocalTimestamp(block.end_at, locale)}`
    }

    return "-"
}

function formatTeamFallback(id, texts, lang) {
    return `${texts?.team_prefix || defaultText(lang, "Team", "Team")} #${id}`
}

function formatMatchTitle(match, texts, lang) {
    /*
     Builds the public title for one upcoming match.
    */
    const team1 = match?.team1Name || (match?.team1Id ? formatTeamFallback(match.team1Id, texts, lang) : texts?.team_one || defaultText(lang, "Team 1", "Team 1"))
    const team2 = match?.team2Name || (match?.team2Id ? formatTeamFallback(match.team2Id, texts, lang) : texts?.team_two || defaultText(lang, "Team 2", "Team 2"))
    return `${team1} vs ${team2}`
}

function formatUpcomingMatchDate(match, texts, lang) {
    /*
     Formats the date label for one upcoming match card.
    */
    const locale = isDutchLang(lang) ? "nl-BE" : "en-US"

    if (match?.weekStartDate) {
        return `${texts?.week_of || defaultText(lang, "Week of", "Week van")} ${match.weekStartDate}`
    }

    if (match?.proposedStartAt) {
        return formatLocalDate(match.proposedStartAt, locale)
    }

    return texts?.date_tbd || defaultText(lang, "Date/time TBD", "Datum/tijd volgt")
}

const styles = { ...formStyles, ...commonStyles, ...dashStyles };

const SHORT_EN = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"];
const SHORT_NL = ["Ma", "Di", "Wo", "Do", "Vr", "Za", "Zo"];

function WeeklyStrip({ blocks, lang }) {
    /*
     Renders the compact weekly availability strip.
    */
    const labels = isDutchLang(lang) ? SHORT_NL : SHORT_EN;
    const activeDays = new Set(blocks.map((block) => Number(block.weekday)));

    return (
        <div className={styles.weeklyStrip}>
            {labels.map((label, index) => {
                const active = activeDays.has(index);
                return (
                    <div key={label} className={`${styles.weeklyDay} ${active ? styles.weeklyDayActive : ""}`}>
                        <span className={styles.weeklyDayLabel}>{label}</span>
                        {active ? <div className={styles.weeklyDayDot} /> : null}
                    </div>
                );
            })}
        </div>
    );
}

export function ProfileTab({ currentUser, setCurrentUser, texts }) {
    /*
     Owns the profile editor and password form state.
    */
    const [form, setForm] = useState({
        firstName: currentUser?.firstName || "",
        lastName: currentUser?.lastName || "",
        dateOfBirth: currentUser?.dateOfBirth || "",
        gender: profileGenderFromUser(currentUser),
        phoneNumber: currentUser?.phoneNumber ?? "",
    });
    const [submitting, setSubmitting] = useState(false);
    const [message, setMessage] = useState({ type: "", text: "" });
    const [passwordForm, setPasswordForm] = useState({
        currentPassword: "",
        newPassword: "",
        repeatPassword: "",
    });
    const [passwordSubmitting, setPasswordSubmitting] = useState(false);
    const [passwordMessage, setPasswordMessage] = useState({
        type: "",
        text: "",
    });
    /*
     Resets the profile form whenever the active account changes.
    */

    useEffect(() => {
        /*
         Resets the form whenever the active user changes.
        */
        setForm({
            firstName: currentUser?.firstName || "",
            lastName: currentUser?.lastName || "",
            dateOfBirth: currentUser?.dateOfBirth || "",
            gender: GENDER_VALUES.includes(currentUser?.gender) ? currentUser.gender : "",
            phoneNumber: currentUser?.phoneNumber ?? "",
        });
    }, [
        currentUser?.firstName,
        currentUser?.lastName,
        currentUser?.dateOfBirth,
        currentUser?.gender,
        currentUser?.phoneNumber,
    ]);

    function onFieldChange(event) {
        /*
         Mirrors one profile field into local state.
        */
        const { name, value } = event.target;
        setForm((previous) => ({ ...previous, [name]: value }));
    }

    function onPasswordFieldChange(event) {
        /*
         Mirrors one password field into local state.
        */
        const { name, value } = event.target;
        setPasswordForm((previous) => ({ ...previous, [name]: value }));
    }
    async function onSubmit(event) {
        /*
         Validates and submits the profile form.
        */
        /*
         Validates and submits the profile form.
        */
        event.preventDefault();
        setMessage({ type: "", text: "" });

        const payload = {
            firstName: form.firstName.trim(),
            lastName: form.lastName.trim(),
            dateOfBirth: form.dateOfBirth || null,
            gender: form.gender,
            phoneNumber: form.phoneNumber.trim(),
        };

        if (!payload.firstName || !payload.lastName) {
            setMessage({
                type: "error",
                text:
                    texts?.profile_required_fields ||
                    "Voornaam en achternaam zijn verplicht.",
            });
            return;
        }

        if (!GENDER_VALUES.includes(payload.gender)) {
            setMessage({
                type: "error",
                text: texts?.profile_gender_required || "Gender is required.",
            });
            return;
        }

        if (!payload.phoneNumber) {
            setMessage({
                type: "error",
                text: texts?.profile_phone_required || "Phone number is required.",
            });
            return;
        }

        setSubmitting(true);
        try {
            const response = await fetch("/api/me", {
                method: "PATCH",
                credentials: "include",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });

            let body = {};
            try {
                body = await response.json();
            } catch {
                body = {};
            }

            if (!response.ok) {
                throw new Error(
                    body?.message ||
                        texts?.profile_update_failed ||
                        "Profiel kon niet worden bijgewerkt.",
                );
            }

            const updatedAccount = body?.account;
            if (updatedAccount) {
                setCurrentUser?.(updatedAccount);
            }

            setMessage({
                type: "success",
                text:
                    texts?.profile_updated_success ||
                    "Profiel succesvol bijgewerkt.",
            });
        } catch (error) {
            setMessage({
                type: "error",
                text:
                    error?.message ||
                    texts?.profile_update_failed ||
                    "Profiel kon niet worden bijgewerkt.",
            });
        } finally {
            setSubmitting(false);
        }
    }

    async function onPasswordSubmit(event) {
        /*
         Validates and submits the password change form.
        */
        event.preventDefault();
        setPasswordMessage({ type: "", text: "" });

        if (!passwordForm.currentPassword || !passwordForm.newPassword) {
            setPasswordMessage({
                type: "error",
                text:
                    texts?.current_and_new_password_required ||
                    "Huidig wachtwoord en nieuw wachtwoord zijn verplicht.",
            });
            return;
        }

        if (passwordForm.newPassword !== passwordForm.repeatPassword) {
            setPasswordMessage({
                type: "error",
                text:
                    texts?.passwords_do_not_match ||
                    "Wachtwoorden komen niet overeen.",
            });
            return;
        }

        setPasswordSubmitting(true);
        try {
            const response = await fetch("/api/me/password", {
                method: "PATCH",
                credentials: "include",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    currentPassword: passwordForm.currentPassword,
                    password: passwordForm.newPassword,
                    repeatPassword: passwordForm.repeatPassword,
                }),
            });

            let body = {};
            try {
                body = await response.json();
            } catch {
                body = {};
            }

            if (!response.ok) {
                throw new Error(
                    body?.message ||
                        texts?.password_update_failed ||
                        "Wachtwoord kon niet worden bijgewerkt.",
                );
            }

            setPasswordForm({
                currentPassword: "",
                newPassword: "",
                repeatPassword: "",
            });
            setPasswordMessage({
                type: "success",
                text:
                    texts?.password_updated_success ||
                    "Wachtwoord succesvol bijgewerkt.",
            });
        } catch (error) {
            setPasswordMessage({
                type: "error",
                text:
                    error?.message ||
                    texts?.password_update_failed ||
                    "Wachtwoord kon niet worden bijgewerkt.",
            });
        } finally {
            setPasswordSubmitting(false);
        }
    }

    return (
        <div className={`${styles.profileStack} ${styles.contentFade}`}>
            <article className={styles.panel}>
                <h3 className={styles.panelTitle}>
                    {texts?.profile_title || "My Profile"}
                </h3>
                <p className={styles.muted}>
                    {texts?.profile_description ||
                        "Update your personal information."}
                </p>

                <form className={styles.form} onSubmit={onSubmit}>
                    <div className={styles.formRow}>
                        <label className={styles.formLabel}>
                            {texts?.first_name || "First name"}
                            <input
                                className={styles.formInput}
                                type="text"
                                name="firstName"
                                value={form.firstName}
                                onChange={onFieldChange}
                                required
                            />
                        </label>

                        <label className={styles.formLabel}>
                            {texts?.last_name || "Last name"}
                            <input
                                className={styles.formInput}
                                type="text"
                                name="lastName"
                                value={form.lastName}
                                onChange={onFieldChange}
                                required
                            />
                        </label>
                    </div>

                    <div className={styles.formRow}>
                        <label className={styles.formLabel}>
                            {texts?.email || "Email"}
                            <input
                                className={styles.formInput}
                                type="email"
                                value={currentUser?.email || ""}
                                disabled
                            />
                        </label>

                        <label className={styles.formLabel}>
                            {texts?.date_of_birth || "Date of birth"}
                            <input
                                className={styles.formInput}
                                type="date"
                                name="dateOfBirth"
                                value={form.dateOfBirth || ""}
                                onChange={onFieldChange}
                            />
                        </label>
                    </div>

                    <div className={styles.formRow}>
                        <label className={styles.formLabel}>
                            {texts?.gender || "Gender"}
                            <select
                                className={styles.formInput}
                                name="gender"
                                required
                                value={form.gender}
                                onChange={onFieldChange}
                            >
                                <option value="" disabled>
                                    {texts?.select_gender || "Select gender"}
                                </option>
                                {GENDER_SELECT_OPTIONS.map((opt) => (
                                    <option key={opt.value} value={opt.value}>
                                        {texts?.[GENDER_TEXT_KEYS[opt.value]] || opt.label}
                                    </option>
                                ))}
                            </select>
                        </label>

                        <label className={styles.formLabel}>
                            {texts?.phone_number || "Phone number"}
                            <input
                                className={styles.formInput}
                                type="tel"
                                name="phoneNumber"
                                required
                                autoComplete="tel"
                                maxLength={64}
                                value={form.phoneNumber}
                                onChange={onFieldChange}
                            />
                        </label>
                    </div>

                    <div className={styles.formActions}>
                        <button
                            className={styles.submitButton}
                            type="submit"
                            disabled={submitting}
                        >
                            {submitting
                                ? texts?.saving || "Saving..."
                                : texts?.save_changes || "Save changes"}
                        </button>
                    </div>
                </form>

                {message.text ? (
                    <p
                        className={`${styles.notice} ${
                            message.type === "error"
                                ? styles.noticeError
                                : styles.noticeSuccess
                        }`}
                    >
                        {message.text}
                    </p>
                ) : null}
            </article>

            <article className={styles.panel}>
                <h3 className={styles.panelTitle}>
                    {texts?.change_password_title || "Change password"}
                </h3>

                <form className={styles.form} onSubmit={onPasswordSubmit}>
                    <label className={styles.formLabel}>
                        {texts?.current_password || "Current password"}
                        <input
                            className={styles.formInput}
                            type="password"
                            name="currentPassword"
                            value={passwordForm.currentPassword}
                            onChange={onPasswordFieldChange}
                            required
                        />
                    </label>

                    <div className={styles.formRow}>
                        <label className={styles.formLabel}>
                            {texts?.new_password || "New password"}
                            <input
                                className={styles.formInput}
                                type="password"
                                name="newPassword"
                                value={passwordForm.newPassword}
                                onChange={onPasswordFieldChange}
                                minLength={6}
                                required
                            />
                        </label>

                        <label className={styles.formLabel}>
                            {texts?.repeat_password || "Repeat password"}
                            <input
                                className={styles.formInput}
                                type="password"
                                name="repeatPassword"
                                value={passwordForm.repeatPassword}
                                onChange={onPasswordFieldChange}
                                minLength={6}
                                required
                            />
                        </label>
                    </div>

                    <div className={styles.formActions}>
                        <button
                            className={styles.submitButton}
                            type="submit"
                            disabled={passwordSubmitting}
                        >
                            {passwordSubmitting
                                ? texts?.saving || "Saving..."
                                : texts?.update_password || "Update password"}
                        </button>
                    </div>
                </form>

                {passwordMessage.text ? (
                    <p
                        className={`${styles.notice} ${
                            passwordMessage.type === "error"
                                ? styles.noticeError
                                : styles.noticeSuccess
                        }`}
                    >
                        {passwordMessage.text}
                    </p>
                ) : null}
            </article>
        </div>
    );
}

//  Overview Tab

export function OverviewTab({
    myClubs,
    myRequests,
    pendingJoinRequestClubIds,
    incomingJoinRequests,
    teamJoinRequestCount = 0,
    clubInvitationCount = 0,
    activeMatchProposalCount = 0,
    upcomingMatches = [],
    texts,
    lang = "en",
}) {
    const highlightItems = [
        {
            label: texts?.sent_club_requests || defaultText(lang, "Club requests sent", "Verzonden clubaanvragen"),
            value: myRequests.length,
            description: texts?.sent_club_requests_hint || defaultText(
                lang,
                "Requests you sent to join clubs.",
                "Aanvragen die jij hebt ingediend om lid te worden van clubs.",
            ),
        },
        {
            label: texts?.pending_club_approvals || defaultText(lang, "Waiting for club approval", "Wachten op clubgoedkeuring"),
            value: pendingJoinRequestClubIds.size,
            description: texts?.pending_club_approvals_hint || defaultText(
                lang,
                "Your club join requests that are still pending.",
                "Jouw clubaanvragen die nog in behandeling zijn.",
            ),
        },
        {
            label: texts?.incoming_join_requests || defaultText(lang, "Club requests to review", "Clubaanvragen om te beoordelen"),
            value: incomingJoinRequests.length,
            description: texts?.incoming_join_requests_hint || defaultText(
                lang,
                "Players waiting for a club owner decision.",
                "Spelers die wachten op een beslissing van een clubeigenaar.",
            ),
        },
        {
            label: texts?.team_join_requests || defaultText(lang, "Team invites", "Teamuitnodigingen"),
            value: teamJoinRequestCount,
            description: texts?.team_join_requests_hint || defaultText(
                lang,
                "Invitations for you to join a team as a player.",
                "Uitnodigingen om als speler bij een team aan te sluiten.",
            ),
        },
        {
            label: texts?.ladder_invites || defaultText(lang, "Ladder and club invites", "Ladder- en clubuitnodigingen"),
            value: clubInvitationCount,
            description: texts?.ladder_invites_hint || defaultText(
                lang,
                "Invitations for teams you manage to join a club or ladder.",
                "Uitnodigingen voor teams die jij beheert om bij een club of ladder te komen.",
            ),
        },
        {
            label: texts?.match_proposals_to_check || defaultText(lang, "Match proposals", "Wedstrijdvoorstellen"),
            value: activeMatchProposalCount,
            description: texts?.match_proposals_to_check_hint || defaultText(
                lang,
                "Visible active proposals that may need accepting, scoring, or follow-up.",
                "Zichtbare actieve voorstellen die mogelijk acceptatie, score-invoer of opvolging nodig hebben.",
            ),
        },
        {
            label: texts?.upcoming_matches || defaultText(lang, "Upcoming matches", "Aankomende wedstrijden"),
            value: upcomingMatches.length,
            description: texts?.upcoming_matches_hint || defaultText(
                lang,
                "Scheduled matches from your dashboard overview.",
                "Geplande wedstrijden uit je dashboardoverzicht.",
            ),
        },
    ];

    return (
        <div className={`${styles.contentGrid} ${styles.contentFade}`}>
            <article className={styles.panel}>
                <h3 className={styles.panelTitle}>{texts?.my_clubs || "My Clubs"}</h3>

                {myClubs.length === 0 ? (
                    <p className={styles.muted}>{texts?.no_clubs_yet || "You are not a member of any club yet."}</p>
                ) : (
                    <ul className={styles.list}>
                        {myClubs.map((club) => {
                            const clubId = club?.id ?? club?.club_id;
                            return (
                                <li className={styles.listItem} key={clubId}>
                                    <div>
                                        <p className={styles.primaryText}>{club?.name || `Club #${clubId}`}</p>
                                        <p className={styles.secondaryText}>
                                            {(club?.membership_status || texts?.member_status || "member").toString()}
                                        </p>
                                    </div>
                                    <Link className={styles.linkButton} to={`/clubs/${clubId}`}>
                                        {texts?.open || defaultText(lang, "Open", "Openen")}
                                    </Link>
                                </li>
                            );
                        })}
                    </ul>
                )}
            </article>

            <article className={styles.panel}>
                <h3 className={styles.panelTitle}>{texts?.quick_highlights || defaultText(lang, "Request Overview", "Aanvragen overzicht")}</h3>
                <div className={styles.metrics}>
                    {highlightItems.map((item) => (
                        <div className={styles.metricCard} key={item.label}>
                            <p className={styles.metricLabel}>{item.label}</p>
                            <p className={styles.metricValue}>{item.value}</p>
                            <p className={styles.secondaryText}>{item.description}</p>
                        </div>
                    ))}
                </div>
            </article>
        </div>
    );
}

//  Search Tab

export function SearchTab({
    searchTerm,
    onSearchChange,
    discoverLoading,
    discoverError,
    filteredDiscoverClubs,
    myClubIds,
    pendingJoinRequestClubIds,
    clubJoinrequest,
    onRequestSubmitted,
    texts,
    lang = "en",
}) {
    const [processingClubId, setProcessingClubId] = useState(null)
    const [actionMessage, setActionMessage] = useState(null)

    async function handleClubRequest(clubId) {
        /*
         Sends a join request and refreshes the dashboard lists afterwards.
        */
        setProcessingClubId(clubId)
        setActionMessage(null)
        try {
            await clubJoinrequest(clubId)
            try {
                await onRequestSubmitted?.()
            } catch {
                // Refresh failures should not hide a successful join request.
            }
            setActionMessage({
                type: "success",
                text: texts?.join_request_sent || defaultText(lang, "Request sent.", "Aanvraag verstuurd."),
            })
        } catch (error) {
            setActionMessage({
                type: "error",
                text: error?.message || texts?.could_not_request_join || defaultText(lang, "Could not send request.", "Aanvraag versturen mislukt."),
            })
        } finally {
            setProcessingClubId(null)
        }
    }

    return (
        <article className={`${styles.panel} ${styles.contentFade}`}>
            <div className={styles.panelTopRow}>
                <h3 className={styles.panelTitle}>{texts?.search_clubs || defaultText(lang, "Search Clubs", "Zoek clubs")}</h3>
                <span className={styles.counter}>{filteredDiscoverClubs.length}</span>
            </div>

            <input
                className={styles.searchInput}
                type="search"
                value={searchTerm}
                onChange={(event) => onSearchChange(event.target.value)}
                placeholder={texts?.search_by_name || defaultText(lang, "Search by club name", "Zoek op clubnaam")}
                aria-label={texts?.search_clubs || defaultText(lang, "Search clubs", "Zoek clubs")}
            />

            {discoverLoading ? <p className={styles.muted}>{texts?.loading_clubs || defaultText(lang, "Loading clubs...", "Clubs laden...")}</p> : null}
            {discoverError ? <p className={styles.warning}>{discoverError}</p> : null}

            {!discoverLoading && !discoverError ? (
                filteredDiscoverClubs.length === 0 ? (
                    <p className={styles.muted}>{texts?.no_clubs_found || defaultText(lang, "No clubs found.", "Geen clubs gevonden.")}</p>
                ) : (
                    <div className={styles.discoverGrid}>
                        {filteredDiscoverClubs.map((club) => {
                            const clubId = Number(club?.id);
                            const isJoined = myClubIds.has(clubId);
                            const hasPendingRequest = pendingJoinRequestClubIds.has(clubId);

                            return (
                                <div className={styles.discoverCard} key={clubId}>
                                    <p className={styles.primaryText}>
                                        {club?.name || `${texts?.club_prefix || defaultText(lang, "Club", "Club")} #${clubId}`}
                                    </p>

                                    <div className={styles.actionRow}>
                                        {isJoined ? (
                                            <span className={`${styles.statusPill} ${styles.statusApproved}`}>
                                                {texts?.joined || defaultText(lang, "Joined", "Lid")}
                                            </span>
                                        ) : null}

                                        {!isJoined && hasPendingRequest ? (
                                            <span className={`${styles.statusPill} ${styles.statusPending}`}>
                                                {texts?.status_pending || defaultText(lang, "Pending", "In afwachting")}
                                            </span>
                                        ) : null}

                                        {!isJoined && !hasPendingRequest ? (
                                                <button
                                                    className={styles.primaryButton}
                                                    type="button"
                                                    onClick={() => handleClubRequest(clubId)}
                                                    disabled={processingClubId === clubId}
                                                >
                                                    {processingClubId === clubId
                                                        ? (texts?.submitting || defaultText(lang, "Sending...", "Bezig..."))
                                                        : (texts?.request_to_join || defaultText(lang, "Request to Join", "Lidmaatschap aanvragen"))}
                                                </button>
                                        ) : null}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )
            ) : null}

            {actionMessage ? (
                <p className={`${styles.notice} ${actionMessage.type === "error" ? styles.noticeError : styles.noticeSuccess}`}>
                    {actionMessage.text}
                </p>
            ) : null}
        </article>
    );
}

export function RequestsTab({
    myRequests,
    texts,
    lang = "en",
}) {
    return (
        <article className={`${styles.panel} ${styles.contentFade}`}>
            <div className={styles.panelTopRow}>
                <h3 className={styles.panelTitle}>{texts?.my_join_requests || defaultText(lang, "My Join Requests", "Mijn aanvragen")}</h3>
                <span className={styles.counter}>{myRequests.length}</span>
            </div>

            {myRequests.length === 0 ? (
                <p className={styles.muted}>{texts?.no_join_requests_yet || defaultText(lang, "No join requests yet.", "Nog geen aanvragen.")}</p>
            ) : (
                <ul className={styles.list}>
                    {myRequests.map((request) => {
                        const requestId = request?.id ?? `${request?.club_id}-${request?.status}`;
                        const requestState = request?.status || "pending";

                        return (
                            <li key={requestId} className={styles.listItem}>
                                <div>
                                    <p className={styles.primaryText}>
                                        {request?.club_name || request?.club?.name || texts?.unknown_club || defaultText(lang, "Unknown club", "Onbekende club")}
                                    </p>
                                    <p className={styles.secondaryText}>
                                        {(texts?.requested_prefix || defaultText(lang, "Requested", "Aangevraagd")) + ":"} {request?.requested_at || "-"}
                                    </p>
                                </div>

                                <span className={`${styles.statusPill} ${statusClass(requestState)}`}>
                                    {statusLabel(requestState, texts)}
                                </span>
                            </li>
                        );
                    })}
                </ul>
            )}
        </article>
    );
}

//  Create Club Tab

export function CreateClubTab({
    clubRequestForm,
    clubRequestSubmitting,
    clubRequestMessage,
    onFieldChange,
    onCitySelect,
    onSubmit,
    texts,
    sportTypes = [],
    lang = "en",
}) {
    return (
        /* Removed the sidebar logic entirely */
        <section className={`${styles.singleColumnLayout} ${styles.contentFade}`}>
            <article className={styles.fullWidthPanel}>
                <h3 className={styles.panelTitle}>{texts?.request_your_club || defaultText(lang, "Request Your Own Club", "Vraag je eigen club aan")}</h3>
                <form className={styles.form} onSubmit={onSubmit}>
                    <div className={styles.formGroup}>
                        <label className={styles.formLabel}>{texts?.club_name || defaultText(lang, "Club Name", "Clubnaam")}</label>
                        <input
                            className={styles.formInput}
                            type="text"
                            name="name"
                            value={clubRequestForm.name}
                            onChange={onFieldChange}
                            placeholder={texts?.club_name_placeholder || defaultText(lang, "What is your club's name?", "Wat is de naam van je club?")}
                            required
                        />
                    </div>

                    <div className={styles.formRow}>
                        <div className={styles.formGroup}>
                            <label className={styles.formLabel}>{texts?.city || defaultText(lang, "City", "Stad")}</label>
                            <CityAutocompleteField
                                value={clubRequestForm.city}
                                onChange={onFieldChange}
                                onSelect={onCitySelect}
                                placeholder={texts?.city_placeholder || defaultText(lang, "City where your club is based", "Stad waar je club gevestigd is")}
                                required
                            />
                        </div>

                        <div className={styles.formGroup}>
                            <label className={styles.formLabel}>{texts?.main_sport || defaultText(lang, "Main Sport", "Hoofdsport")}</label>
                            <select
                                className={styles.formInput}
                                name="sport_type_id" 
                                value={clubRequestForm.sport_type_id || ""}
                                onChange={onFieldChange}
                                required
                            >
                                <option value="" disabled>{texts?.select_sport_placeholder || defaultText(lang, "Select a sport", "Selecteer een sport")}</option>
                                {sportTypes.map((sport) => (
                                    <option key={sport.id} value={sport.id}>{sport.name}</option>
                                ))}
                            </select>
                        </div>
                    </div>

                    <div className={styles.formGroup}>
                        <label className={styles.formLabel}>{texts?.description || defaultText(lang, "Description", "Beschrijving")}</label>
                        <textarea
                            className={styles.formTextarea}
                            name="description"
                            value={clubRequestForm.description}
                            onChange={onFieldChange}
                            placeholder={texts?.description_placeholder || defaultText(lang, "Tell us about your club...", "Vertel ons over je club...")}
                            rows={6} // Made slightly taller since we have more room
                            required
                        />
                    </div>

                    <div className={styles.formActions}>
                        <button type="submit" className={styles.submitButton} disabled={clubRequestSubmitting}>
                            {clubRequestSubmitting ? texts?.submitting : texts?.submit_club_request}
                        </button>
                    </div>
                </form>

                {clubRequestMessage.text && (
                    <p className={`${styles.notice} ${clubRequestMessage.type === "error" ? styles.noticeError : styles.noticeSuccess}`}>
                        {clubRequestMessage.text}
                    </p>
                )}
            </article>
        </section>
    );
}
export default CreateClubTab;

export function ManageClubsTab({
    myClubs,
    incomingJoinRequests,
    decideJoinrequest,
    isClubOwner,
    onGoSettings,
    onRequestsUpdated,
    texts,
    lang = "en",
}) {
    const [processingRequest, setProcessingRequest] = useState(null);
    const [actionMessage, setActionMessage] = useState(null);
    const ownedClubs = myClubs.filter(club => club.membership_status === "owner");

    async function handleRequestDecision(req, status) {
        /*
         Updates one join request and refreshes the list when done.
        */
        const key = `${req.club_id}-${req.user_id}-${status}`;
        setProcessingRequest(key);
        setActionMessage(null);
        try {
            await decideJoinrequest(req.club_id, req.user_id, status);
            try {
                await onRequestsUpdated?.()
            } catch {
                // Refresh failures should not hide a successful moderation decision.
            }
            setActionMessage({
                type: "success",
                text: texts?.request_updated || defaultText(lang, "Request updated.", "Aanvraag bijgewerkt."),
            });
        } catch (error) {
            setActionMessage({
                type: "error",
                text: error?.message || texts?.could_not_update_request || defaultText(lang, "Could not update request.", "Aanvraag bijwerken mislukt."),
            });
        } finally {
            setProcessingRequest(null);
        }
    }

    if (!isClubOwner && ownedClubs.length === 0) {
        return (
            <div className={styles.panel} style={{ textAlign: 'center', padding: '40px' }}>
                <p className={styles.muted}>
                    {texts?.no_clubs_owned || defaultText(lang, "You don't own any clubs yet.", "Je bent nog geen eigenaar van een club.")}
                </p>
            </div>
        );
    }

    return (
        <div className={`${styles.contentFade} ${styles.manageClubsLayout}`}>
            <article className={styles.panel}>
                <div className={styles.panelTopRow}>
                    <h3 className={styles.panelTitle}>{texts?.your_clubs || defaultText(lang, "Your clubs", "Jouw eigen clubs")}</h3>
                    <span className={styles.counter}>{ownedClubs.length}</span>
                </div>

                {ownedClubs.length === 0 ? (
                    <p className={styles.muted}>{texts?.no_clubs_owned || defaultText(lang, "You don't own any clubs yet.", "Je bent nog geen eigenaar van een club.")}</p>
                ) : (
                    <ul className={styles.list}>
                        {ownedClubs.map(club => (
                            <li key={club.id} className={styles.listItem}>
                                <div>
                                    <p className={styles.primaryText}>{club.name}</p>
                                    <p className={styles.secondaryText}>
                                        {club.city || texts?.unknown_city || defaultText(lang, "Unknown city", "Onbekende stad")}
                                        {club.sport || club.sport_type_id ? ` · ${club.sport || `${texts?.sport_prefix || defaultText(lang, "Sport", "Sport")} #${club.sport_type_id}`}` : ""}
                                    </p>
                                </div>
                                <button
                                    onClick={() => onGoSettings(club.id)}
                                    className={styles.linkButton}
                                >
                                    {texts?.settings || defaultText(lang, "Settings", "Instellingen")}
                                </button>
                            </li>
                        ))}
                    </ul>
                )}
            </article>

            <article className={styles.panel}>
                <div className={styles.panelTopRow}>
                    <h3 className={styles.panelTitle}>
                        {texts?.incoming_join_requests || defaultText(lang, "Incoming join requests", "Binnenkomende aanmeldverzoeken")}
                    </h3>
                    <span className={styles.counter}>{incomingJoinRequests.length}</span>
                </div>

                {incomingJoinRequests.length === 0 ? (
                    <p className={styles.muted}>{texts?.no_incoming_requests || defaultText(lang, "No incoming requests yet.", "Nog geen binnenkomende aanvragen.")}</p>
                ) : (
                    <ul className={styles.requestList}>
                        {incomingJoinRequests.map((req, index) => (
                            <li className={styles.requestCard} key={`${req.club_id}-${req.user_id}-${index}`}>
                                <div className={styles.requestContent}>
                                    <p className={styles.primaryText}>
                                        <strong>{req.user_name}</strong> {texts?.wants_to_join || defaultText(lang, "wants to join", "wil lid worden van")} <strong>{req.club_name}</strong>
                                    </p>
                                </div>
                                <div className={styles.requestActions}>
                                    <button
                                        className={styles.submitButton}
                                        type="button"
                                        disabled={processingRequest === `${req.club_id}-${req.user_id}-approved`}
                                        onClick={() => handleRequestDecision(req, "approved")}
                                    >
                                        {processingRequest === `${req.club_id}-${req.user_id}-approved`
                                            ? (texts?.saving || defaultText(lang, "Saving...", "Bezig..."))
                                            : (texts?.approve || defaultText(lang, "Approve", "Goedkeuren"))}
                                    </button>

                                    <button
                                        className={styles.submitButton}
                                        type="button"
                                        style={{ filter: 'grayscale(1) brightness(0.7)' }}
                                        disabled={processingRequest === `${req.club_id}-${req.user_id}-rejected`}
                                        onClick={() => handleRequestDecision(req, "rejected")}
                                    >
                                        {processingRequest === `${req.club_id}-${req.user_id}-rejected`
                                            ? (texts?.saving || defaultText(lang, "Saving...", "Bezig..."))
                                            : (texts?.reject || defaultText(lang, "Reject", "Afwijzen"))}
                                    </button>
                                </div>
                            </li>
                        ))}
                    </ul>
                )}

                {actionMessage ? (
                    <p className={`${styles.notice} ${actionMessage.type === "error" ? styles.noticeError : styles.noticeSuccess}`}>
                        {actionMessage.text}
                    </p>
                ) : null}
            </article>
        </div>
    );
}
//  Teams Tab


export function AvailabilityTab({
    availabilityBlocks,
    upcomingMatches,
    availabilityForm,
    availabilityLoading,
    availabilitySubmitting,
    availabilityMessage,
    onAvailabilityFieldChange,
    onAvailabilitySubmit,
    onAvailabilityDelete,
    weekdayOptions,
    texts,
    lang = "en",
}) {
    const { theme } = useThemeContext();
    const isLight = theme === "light";

    return (
        <section className={`${styles.availabilityLayout} ${styles.contentFade}`}>
            <article className={styles.panel}>
                <h3 className={styles.panelTitle}>
                        {texts?.availability_title || defaultText(lang, "My Availability", "Mijn beschikbaarheid")}
                </h3>
                <form className={styles.form} onSubmit={onAvailabilitySubmit}>
                    <label className={styles.formLabel}>
                        {texts?.weekday || defaultText(lang, "Weekday", "Weekdag")}
                        <select
                            className={styles.formInput}
                            name="weekday"
                            value={availabilityForm.weekday}
                            onChange={onAvailabilityFieldChange}
                            required
                        >
                            <option value="">{texts?.select_weekday || defaultText(lang, "Choose a weekday", "Kies een weekdag")}</option>
                            {(weekdayOptions || (isDutchLang(lang) ? NL_WEEKDAY_LABELS : EN_WEEKDAY_LABELS).map((label, index) => ({ value: String(index), label }))).map((option) => (
                                <option key={option.value} value={option.value}>
                                    {option.label}
                                </option>
                            ))}
                        </select>
                    </label>

                    <div className={styles.formRow}>
                        <label className={styles.formLabel}>
                            {texts?.start_time || defaultText(lang, "Start time", "Starttijd")}
                            <input
                                className={styles.formInput}
                                type="time"
                                name="startTime"
                                value={availabilityForm.startTime}
                                onChange={onAvailabilityFieldChange}
                                required
                            />
                        </label>
                        <label className={styles.formLabel}>
                            {texts?.end_time || defaultText(lang, "End time", "Eindtijd")}
                            <input
                                className={styles.formInput}
                                type="time"
                                name="endTime"
                                value={availabilityForm.endTime}
                                onChange={onAvailabilityFieldChange}
                                required
                            />
                        </label>
                    </div>

                    <div className={styles.formActions}>
                        <button
                            className={styles.submitButton}
                            type="submit"
                            disabled={availabilitySubmitting}
                        >
                            {availabilitySubmitting
                                ? texts?.adding || defaultText(lang, "Adding...", "Toevoegen...")
                                : texts?.add_availability_block || defaultText(lang, "Add availability block", "Beschikbaarheidsblok toevoegen")}
                        </button>
                    </div>
                </form>

                {availabilityMessage.text ? (
                    <p
                        className={`${styles.notice} ${
                            availabilityMessage.type === "error"
                                ? styles.noticeError
                                : availabilityMessage.type === "success"
                                  ? styles.noticeSuccess
                                  : styles.noticeInfo
                        }`}
                    >
                        {availabilityMessage.text}
                    </p>
                ) : null}
            </article>

            <div className={styles.availabilityStack}>
                <article className={styles.panel}>
                    <div className={styles.panelTopRow}>
                        <h3 className={styles.panelTitle}>
                            {texts?.availability_blocks || defaultText(lang, "Your blocks", "Jouw blokken")}
                        </h3>
                        <span className={styles.counter}>{availabilityBlocks.length}</span>
                    </div>

                    {!availabilityLoading && (
                        <WeeklyStrip blocks={availabilityBlocks} lang={lang} />
                    )}

                    {availabilityLoading ? (
                        <p className={styles.muted}>{texts?.loading || defaultText(lang, "Loading...", "Laden...")}</p>
                    ) : null}

                    {!availabilityLoading && availabilityBlocks.length === 0 ? (
                        <p className={styles.muted}>
                            {texts?.no_availability_blocks || defaultText(lang, "No availability blocks yet.", "Nog geen beschikbaarheidsblokken.")}
                        </p>
                    ) : null}

                    {!availabilityLoading && availabilityBlocks.length > 0 ? (
                        <ul className={styles.availabilityList}>
                            {availabilityBlocks.map((block) => (
                                <li className={styles.availabilityCard} key={block.id}>
                                    <div>
                                        <p
                                            className={styles.primaryText}
                                            style={isLight ? { color: "#020617", WebkitTextFillColor: "#020617" } : undefined}
                                        >
                                            {formatWeeklyAvailability(block, lang)}
                                        </p>
                                        <p
                                            className={styles.secondaryText}
                                            style={isLight ? { color: "#475569", WebkitTextFillColor: "#475569" } : undefined}
                                        >
                                            {texts?.availability_block_detail || defaultText(lang, "Weekly recurring block", "Wekelijks terugkerend blok")}
                                        </p>
                                    </div>
                                    <button
                                        className={styles.primaryButton}
                                        type="button"
                                        onClick={() => onAvailabilityDelete(block.id)}
                                    >
                                        {texts?.delete || defaultText(lang, "Delete", "Verwijderen")}
                                    </button>
                                </li>
                            ))}
                        </ul>
                    ) : null}
                </article>

                <article className={styles.panel}>
                    <div className={styles.panelTopRow}>
                        <h3 className={styles.panelTitle}>
                            {texts?.availability_upcoming_matches || defaultText(lang, "Upcoming matches", "Aankomende wedstrijden")}
                        </h3>
                        <span className={styles.counter}>{upcomingMatches.length}</span>
                    </div>

                    {upcomingMatches.length === 0 ? (
                        <p className={styles.muted}>
                            {texts?.no_upcoming_matches || defaultText(lang, "No upcoming matches scheduled.", "Er staan nog geen aankomende wedstrijden gepland.")}
                        </p>
                    ) : (
                        <ul className={styles.availabilityList}>
                            {upcomingMatches.map((match) => (
                                <li className={styles.availabilityCard} key={match.id}>
                                    <div>
                                        <p
                                            className={styles.primaryText}
                                            style={isLight ? { color: "#020617", WebkitTextFillColor: "#020617" } : undefined}
                                        >
                                            {formatMatchTitle(match, texts, lang)}
                                        </p>
                                        <p
                                            className={styles.secondaryText}
                                            style={isLight ? { color: "#475569", WebkitTextFillColor: "#475569" } : undefined}
                                        >
                                            {formatUpcomingMatchDate(match, texts, lang)}
                                        </p>
                                    </div>
                                    <span className={`${styles.statusPill} ${styles.statusApproved}`}>
                                        {match.status?.name || texts?.status_accepted || defaultText(lang, "Accepted", "Geaccepteerd")}
                                    </span>
                                </li>
                            ))}
                        </ul>
                    )}
                </article>
            </div>
        </section>
    )
}
