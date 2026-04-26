import { useEffect, useState } from "react";
import { Link} from "react-router-dom";
import formStyles from "@/style/common/Forms.module.css";
import commonStyles from "@/style/common/Common.module.css";
import dashStyles from "@/style/ClubSettings.module.css";

import {statusClass, statusLabel} from "@/components/dashboard/dashboardUtils.js";

function parseUtcTimestamp(value) {
    if (typeof value !== "string") {
        return null
    }

    const parsed = new Date(value)

    if (Number.isNaN(parsed.getTime())) {
        return null
    }

    return parsed
}

function formatLocalTimestamp(value) {
    const parsed = parseUtcTimestamp(value)
    if (!parsed) {
        return value || "-"
    }

    return parsed.toLocaleString()
}

const WEEKDAY_LABELS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]

function formatWeeklyAvailability(block) {
    const weekdayIndex = Number(block?.weekday)
    const weekdayLabel = block?.weekday_label || WEEKDAY_LABELS[weekdayIndex] || "Day"
    const startTime = block?.start_time || "--:--"
    const endTime = block?.end_time || "--:--"

    if (block?.weekday !== undefined && block?.weekday !== null) {
        return `${weekdayLabel} ${startTime} - ${endTime}`
    }

    if (block?.start_at && block?.end_at) {
        return `${formatLocalTimestamp(block.start_at)} - ${formatLocalTimestamp(block.end_at)}`
    }

    return "-"
}

function formatMatchTitle(match) {
    const team1 = match?.team1Name || (match?.team1Id ? `Team #${match.team1Id}` : "Team 1")
    const team2 = match?.team2Name || (match?.team2Id ? `Team #${match.team2Id}` : "Team 2")
    return `${team1} vs ${team2}`
}

function formatUpcomingMatchDate(match, texts) {
    const start = formatLocalTimestamp(match?.proposedStartAt)
    const end = formatLocalTimestamp(match?.proposedEndAt)

    if (match?.proposedStartAt && match?.proposedEndAt) {
        return `${start} - ${end}`
    }

    if (match?.proposedStartAt) {
        return start
    }

    if (match?.weekStartDate) {
        return `${texts?.week_of || "Week of"} ${match.weekStartDate}`
    }

    return texts?.date_tbd || "Date/time TBD"
}

const styles = { ...formStyles, ...commonStyles, ...dashStyles };

export function ProfileTab({ currentUser, setCurrentUser, texts }) {
    const [form, setForm] = useState({
        firstName: currentUser?.firstName || "",
        lastName: currentUser?.lastName || "",
        dateOfBirth: currentUser?.dateOfBirth || "",
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

    useEffect(() => {
        setForm({
            firstName: currentUser?.firstName || "",
            lastName: currentUser?.lastName || "",
            dateOfBirth: currentUser?.dateOfBirth || "",
        });
    }, [currentUser?.firstName, currentUser?.lastName, currentUser?.dateOfBirth]);

    function onFieldChange(event) {
        const { name, value } = event.target;
        setForm((previous) => ({ ...previous, [name]: value }));
    }

    function onPasswordFieldChange(event) {
        const { name, value } = event.target;
        setPasswordForm((previous) => ({ ...previous, [name]: value }));
    }

    async function onSubmit(event) {
        event.preventDefault();
        setMessage({ type: "", text: "" });

        const payload = {
            firstName: form.firstName.trim(),
            lastName: form.lastName.trim(),
            dateOfBirth: form.dateOfBirth || null,
        };

        if (!payload.firstName || !payload.lastName) {
            setMessage({
                type: "error",
                text:
                    texts?.profile_required_fields ||
                    "First name and last name are required.",
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
                        "Could not update profile.",
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
                    "Profile updated successfully.",
            });
        } catch (error) {
            setMessage({
                type: "error",
                text:
                    error?.message ||
                    texts?.profile_update_failed ||
                    "Could not update profile.",
            });
        } finally {
            setSubmitting(false);
        }
    }

    async function onPasswordSubmit(event) {
        event.preventDefault();
        setPasswordMessage({ type: "", text: "" });

        if (!passwordForm.currentPassword || !passwordForm.newPassword) {
            setPasswordMessage({
                type: "error",
                text:
                    texts?.current_and_new_password_required ||
                    "Current password and new password are required.",
            });
            return;
        }

        if (passwordForm.newPassword !== passwordForm.repeatPassword) {
            setPasswordMessage({
                type: "error",
                text:
                    texts?.passwords_do_not_match ||
                    "Passwords do not match.",
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
                        "Could not update password.",
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
                    "Password updated successfully.",
            });
        } catch (error) {
            setPasswordMessage({
                type: "error",
                text:
                    error?.message ||
                    texts?.password_update_failed ||
                    "Could not update password.",
            });
        } finally {
            setPasswordSubmitting(false);
        }
    }

    return (
        <article className={`${styles.panel} ${styles.contentFade}`}>
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
        </article>
    );
}

//  Overview Tab

export function OverviewTab({ myClubs, myRequests, pendingJoinRequestClubIds, clubCreationRequests, texts }) {
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
                                        {texts?.open || "Open"}
                                    </Link>
                                </li>
                            );
                        })}
                    </ul>
                )}
            </article>

            <article className={styles.panel}>
                <h3 className={styles.panelTitle}>{texts?.quick_highlights || "Quick Highlights"}</h3>
                <div className={styles.metrics}>
                    <div className={styles.metricCard}>
                        <p className={styles.metricLabel}>{texts?.join_requests || "Join requests"}</p>
                        <p className={styles.metricValue}>{myRequests.length}</p>
                    </div>
                    <div className={styles.metricCard}>
                        <p className={styles.metricLabel}>{texts?.pending_join_requests || "Pending join requests"}</p>
                        <p className={styles.metricValue}>{pendingJoinRequestClubIds.size}</p>
                    </div>
                    <div className={styles.metricCard}>
                        <p className={styles.metricLabel}>
                            {texts?.club_registration_requests || "Club registration requests"}
                        </p>
                        <p className={styles.metricValue}>{clubCreationRequests.length}</p>
                    </div>
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
    texts,
}) {
    return (
        <article className={`${styles.panel} ${styles.contentFade}`}>
            <div className={styles.panelTopRow}>
                <h3 className={styles.panelTitle}>{texts?.search_clubs || "Search Clubs"}</h3>
                <span className={styles.counter}>{filteredDiscoverClubs.length}</span>
            </div>

            <input
                className={styles.searchInput}
                type="search"
                value={searchTerm}
                onChange={(event) => onSearchChange(event.target.value)}
                placeholder={texts?.search_by_name || "Search by club name"}
                aria-label={texts?.search_clubs || "Search clubs"}
            />

            {discoverLoading ? <p className={styles.muted}>{texts?.loading_clubs || "Loading clubs..."}</p> : null}
            {discoverError ? <p className={styles.warning}>{discoverError}</p> : null}

            {!discoverLoading && !discoverError ? (
                filteredDiscoverClubs.length === 0 ? (
                    <p className={styles.muted}>{texts?.no_clubs_found || "No clubs found."}</p>
                ) : (
                    <div className={styles.discoverGrid}>
                        {filteredDiscoverClubs.map((club) => {
                            const clubId = Number(club?.id);
                            const isJoined = myClubIds.has(clubId);
                            const hasPendingRequest = pendingJoinRequestClubIds.has(clubId);

                            return (
                                <div className={styles.discoverCard} key={clubId}>
                                    <p className={styles.primaryText}>{club?.name || `Club #${clubId}`}</p>

                                    <div className={styles.actionRow}>
                                        {isJoined ? (
                                            <span className={`${styles.statusPill} ${styles.statusApproved}`}>
                                                {texts?.joined || "Joined"}
                                            </span>
                                        ) : null}

                                        {!isJoined && hasPendingRequest ? (
                                            <span className={`${styles.statusPill} ${styles.statusPending}`}>
                                                {texts?.status_pending || "Pending"}
                                            </span>
                                        ) : null}

                                        {!isJoined && !hasPendingRequest ? (
                                                <button
                                                    className={styles.primaryButton}
                                                    type="button"
                                                    onClick={(e) => {clubJoinrequest(clubId);e.currentTarget.disabled = true;}}>
                                                    {texts?.request_to_join || "Request to Join"}
                                                </button>
                                        ) : null}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )
            ) : null}
        </article>
    );
}

export function RequestsTab({
    myRequests,
    texts
}) {
    return (
        <article className={`${styles.panel} ${styles.contentFade}`}>
            <div className={styles.panelTopRow}>
                <h3 className={styles.panelTitle}>{texts?.my_join_requests || "My Join Requests"}</h3>
                <span className={styles.counter}>{myRequests.length}</span>
            </div>

            {myRequests.length === 0 ? (
                <p className={styles.muted}>{texts?.no_join_requests_yet || "No join requests yet."}</p>
            ) : (
                <ul className={styles.list}>
                    {myRequests.map((request) => {
                        const requestId = request?.id ?? `${request?.club_id}-${request?.status}`;
                        const requestState = request?.status || "pending";

                        return (
                            <li key={requestId} className={styles.listItem}>
                                <div>
                                    <p className={styles.primaryText}>
                                        {request?.club_name || request?.club?.name || texts?.unknown_club || "Unknown club"}
                                    </p>
                                    <p className={styles.secondaryText}>
                                        {(texts?.requested_prefix || "Requested") + ":"} {request?.requested_at || "-"}
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
    onSubmit,
    texts,
    sportTypes = []
}) {
    return (
        /* Removed the sidebar logic entirely */
        <section className={`${styles.singleColumnLayout} ${styles.contentFade}`}>
            <article className={styles.fullWidthPanel}>
                <h3 className={styles.panelTitle}>{texts?.request_your_club || "Request Your Own Club"}</h3>
                <form className={styles.form} onSubmit={onSubmit}>
                    <div className={styles.formGroup}>
                        <label className={styles.formLabel}>{texts?.club_name || "Club Name"}</label>
                        <input
                            className={styles.formInput}
                            type="text"
                            name="name"
                            value={clubRequestForm.name}
                            onChange={onFieldChange}
                            placeholder={texts?.club_name_placeholder || "What is your club's name?"}
                            required
                        />
                    </div>

                    <div className={styles.formRow}>
                        <div className={styles.formGroup}>
                            <label className={styles.formLabel}>{texts?.city || "City"}</label>
                            <input
                                className={styles.formInput}
                                type="text"
                                name="city"
                                value={clubRequestForm.city}
                                onChange={onFieldChange}
                                placeholder={texts?.city_placeholder || "City where your club is based"}
                                required
                            />
                        </div>

                        <div className={styles.formGroup}>
                            <label className={styles.formLabel}>{texts?.main_sport || "Main Sport"}</label>
                            <select
                                className={styles.formInput}
                                name="sport_type_id" 
                                value={clubRequestForm.sport_type_id || ""}
                                onChange={onFieldChange}
                                required
                            >
                                <option value="" disabled>{texts?.select_sport_placeholder || "Select a sport"}</option>
                                {sportTypes.map((sport) => (
                                    <option key={sport.id} value={sport.id}>{sport.name}</option>
                                ))}
                            </select>
                        </div>
                    </div>

                    <div className={styles.formGroup}>
                        <label className={styles.formLabel}>{texts?.description || "Description"}</label>
                        <textarea
                            className={styles.formTextarea}
                            name="description"
                            value={clubRequestForm.description}
                            onChange={onFieldChange}
                            placeholder={texts?.description_placeholder || "Tell us about your club..."}
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
    texts
}) {
    const ownedClubs = myClubs.filter(club => club.membership_status === "owner");

    if (!isClubOwner && ownedClubs.length === 0) {
        return (
            <div className={styles.panel} style={{ textAlign: 'center', padding: '40px' }}>
                <h3 className={styles.panelTitle}>{texts?.manage_clubs_title || "Club Administration"}</h3>
                <p className={styles.muted}>
                    {texts?.no_clubs_owned || "You don't own any clubs yet."}
                </p>
            </div>
        );
    }

    return (
        <div className={`${commonStyles.noStylePleaseFixMe} ${styles.contentFade}`}>
            <h2 className={styles.panelTitle}>{texts?.manage_clubs_title || "Club Administration"}</h2>

            <div className={commonStyles.noStylePleaseFixMe}>
                <section className={commonStyles.noStylePleaseFixMe}>
                    <article className={styles.panel}>
                        <h3 className={styles.panelTitle}>{texts?.your_clubs || "Your Owned Clubs"}</h3>

                        {ownedClubs.length === 0 ? (
                            <p className={styles.muted}>You haven't been assigned as an owner to any clubs yet.</p>
                        ) : (
                            <ul className={styles.list}>
                                {ownedClubs.map(club => (
                                    <li key={club.id} className={styles.listItem}>
                                        <div>
                                            <p className={styles.primaryText}>{club.name}</p>
                                            <p className={styles.secondaryText}>
                                                {club.city} - {club.sport_type_id}
                                            </p>
                                        </div>
                                        <button
                                        onClick={() => onGoSettings(club.id)}
                                        className={styles.linkButton}>
                                            Settings
                                        </button>
                                    </li>
                                ))}
                            </ul>
                        )}
                    </article>
                </section>

                <aside className={commonStyles.noStylePleaseFixMe}>
                    <article className={styles.panel}>
                        <div className={styles.panelTopRow}>
                            <h3 className={styles.panelTitle}>
                                {texts?.incoming_join_requests || "Incoming Join Requests"}
                            </h3>
                            <span className={styles.counter}>{incomingJoinRequests.length}</span>
                        </div>

                        {incomingJoinRequests.length === 0 ? (
                            <p className={styles.muted}>No pending join requests.</p>
                        ) : (
                            <ul className={styles.list}>
                                {incomingJoinRequests.map((req, index) => (
                                    <li className={styles.listItem} key={index}>
                                        <div>
                                            <p className={styles.primaryText}>
                                                <strong>{req.user_name}</strong> wants to join <strong>{req.club_name}</strong>
                                            </p>
                                        </div>
                                        <div className={styles.actionRow} style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
                                            <button
                                            className={styles.submitButton}
                                            type="button"
                                            onClick={(e) => {
                                                // Find all buttons in this specific div and disable them
                                                const row = e.currentTarget.closest(`.${commonStyles.noStylePleaseFixMe}`);
                                                row.querySelectorAll('button').forEach(btn => btn.disabled = true);

                                                decideJoinrequest(req.club_id, req.user_id, "approved");
                                            }}>
                                            {texts?.approve || "Approve"}
                                        </button>

                                        <button
                                            className={styles.submitButton}
                                            type="button"
                                            style={{ filter: 'grayscale(1) brightness(0.7)' }}
                                            onClick={(e) => {
                                                const row = e.currentTarget.closest(`.${commonStyles.noStylePleaseFixMe}`);
                                                row.querySelectorAll('button').forEach(btn => btn.disabled = true);

                                                decideJoinrequest(req.club_id, req.user_id, "rejected");
                                            }}>
                                            {texts?.reject || "Reject"}
                                        </button>
                                        </div>
                                    </li>
                                ))}
                            </ul>
                        )}
                    </article>
                </aside>
            </div>
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
}) {
    return (
        <section className={`${styles.createClubLayout} ${styles.contentFade}`}>
            <article className={styles.panel}>
                <h3 className={styles.panelTitle}>
                    {texts?.availability_title || "My Availability"}
                </h3>
                <form className={styles.form} onSubmit={onAvailabilitySubmit}>
                    <div className={styles.formRow}>
                        <label className={styles.formLabel}>
                            {texts?.weekday || "Weekday"}
                            <select
                                className={styles.formInput}
                                name="weekday"
                                value={availabilityForm.weekday}
                                onChange={onAvailabilityFieldChange}
                                required
                            >
                                <option value="">{texts?.select_weekday || "Select weekday"}</option>
                                {(weekdayOptions || WEEKDAY_LABELS.map((label, index) => ({ value: String(index), label }))).map((option) => (
                                    <option key={option.value} value={option.value}>
                                        {option.label}
                                    </option>
                                ))}
                            </select>
                        </label>
                        <label className={styles.formLabel}>
                            {texts?.start_time || "Start time"}
                            <input
                                className={styles.formInput}
                                type="time"
                                name="startTime"
                                value={availabilityForm.startTime}
                                onChange={onAvailabilityFieldChange}
                                required
                            />
                        </label>
                    </div>

                    <label className={styles.formLabel}>
                        {texts?.end_time || "End time"}
                        <input
                            className={styles.formInput}
                            type="time"
                            name="endTime"
                            value={availabilityForm.endTime}
                            onChange={onAvailabilityFieldChange}
                            required
                        />
                    </label>

                    <div className={styles.formActions}>
                        <button
                            className={styles.submitButton}
                            type="submit"
                            disabled={availabilitySubmitting}
                        >
                            {availabilitySubmitting
                                ? texts?.adding || "Adding..."
                                : texts?.add_availability_block || "Add availability block"}
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

            <div className={commonStyles.noStylePleaseFixMe}>
                <article className={styles.panel}>
                    <div className={styles.panelTopRow}>
                        <h3 className={styles.panelTitle}>
                            {texts?.availability_blocks || "Your blocks"}
                        </h3>
                        <span className={styles.counter}>{availabilityBlocks.length}</span>
                    </div>

                    {availabilityLoading ? (
                        <p className={styles.muted}>{texts?.loading || "Loading..."}</p>
                    ) : null}

                    {!availabilityLoading && availabilityBlocks.length === 0 ? (
                        <p className={styles.muted}>
                            {texts?.no_availability_blocks || "No availability blocks yet."}
                        </p>
                    ) : null}

                    {!availabilityLoading && availabilityBlocks.length > 0 ? (
                        <ul className={styles.list}>
                            {availabilityBlocks.map((block) => (
                                <li className={styles.listItem} key={block.id}>
                                    <div>
                                        <p className={styles.primaryText}>
                                            {formatWeeklyAvailability(block)}
                                        </p>
                                    </div>
                                    <button
                                        className={styles.primaryButton}
                                        type="button"
                                        onClick={() => onAvailabilityDelete(block.id)}
                                    >
                                        {texts?.delete || "Delete"}
                                    </button>
                                </li>
                            ))}
                        </ul>
                    ) : null}
                </article>

                <article className={styles.panel}>
                    <div className={styles.panelTopRow}>
                        <h3 className={styles.panelTitle}>
                            {texts?.availability_upcoming_matches || "Upcoming matches"}
                        </h3>
                        <span className={styles.counter}>{upcomingMatches.length}</span>
                    </div>

                    {upcomingMatches.length === 0 ? (
                        <p className={styles.muted}>
                            {texts?.no_upcoming_matches || "No upcoming matches scheduled."}
                        </p>
                    ) : (
                        <ul className={styles.list}>
                            {upcomingMatches.map((match) => (
                                <li className={styles.listItem} key={match.id}>
                                    <div>
                                        <p className={styles.primaryText}>{formatMatchTitle(match)}</p>
                                        <p className={styles.secondaryText}>
                                            {formatUpcomingMatchDate(match, texts)}
                                        </p>
                                        <p className={styles.secondaryText}>
                                            {match.location || texts?.unknown_location || "Unknown location"}
                                        </p>
                                    </div>
                                    <span className={`${styles.statusPill} ${styles.statusApproved}`}>
                                        {match.status?.name || texts?.status_accepted || "Accepted"}
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
