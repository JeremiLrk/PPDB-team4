import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import formStyles from "@/style/common/Forms.module.css";
import commonStyles from "@/style/common/Common.module.css";
import dashStyles from "@/style/ClubSettings.module.css";
import dashboardStyles from "@/style/Dashboard.module.css";

import TeamCard from "@/components/dashboard/TeamCard.jsx";
import {statusClass, statusLabel} from "@/components/dashboard/dashboardUtils.js";
import CreateTeamButton from "@/components/team/CreateTeamButton.jsx";

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

// We combine both modules into one proxy object,
// so as not to rewrite every styles.* in the template.
// Dashboard-specific classes (shell, sidebar, …) only cover what
// is not in Common, so there are no collisions.
const styles = { ...formStyles, ...commonStyles, ...dashStyles };

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
    clubCreationRequests,
    onFieldChange,
    onSubmit,
    texts,
    incomingJoinRequests,
    decideJoinrequest,
    isClubOwner
}) {
    return (
        <section className={`${styles.createClubLayout} ${styles.contentFade}`}>
            {/* Left Column: The Form */}
            <article className={styles.panel}>
                <h3 className={styles.panelTitle}>{texts?.request_your_club || "Request Your Own Club"}</h3>
                <form className={styles.form} onSubmit={onSubmit}>
                    <label className={styles.formLabel}>
                        {texts?.club_name || "Club Name"}
                        <input
                            className={styles.formInput}
                            type="text"
                            name="name"
                            value={clubRequestForm.name}
                            onChange={onFieldChange}
                            placeholder={texts?.club_name_placeholder || "What is your club's name?"}
                            required
                        />
                    </label>

                    <div className={styles.formRow}>
                        <label className={styles.formLabel}>
                            {texts?.city || "City"}
                            <input
                                className={styles.formInput}
                                type="text"
                                name="city"
                                value={clubRequestForm.city}
                                onChange={onFieldChange}
                                placeholder={texts?.city_placeholder || "City where your club is based"}
                                required
                            />
                        </label>

                        <label className={styles.formLabel}>
                            {texts?.main_sport || "Main Sport"}
                            <input
                                className={styles.formInput}
                                type="text"
                                name="sport"
                                value={clubRequestForm.sport}
                                onChange={onFieldChange}
                                placeholder={texts?.main_sport_placeholder || "Padel"}
                                required
                            />
                        </label>
                    </div>

                    <label className={styles.formLabel}>
                        {texts?.description || "Description"}
                        <textarea
                            className={styles.formTextarea}
                            name="description"
                            value={clubRequestForm.description}
                            onChange={onFieldChange}
                            placeholder={
                                texts?.description_placeholder ||
                                "Tell us what your club is about and why you want to use our platform"
                            }
                            rows={4}
                            required
                        />
                    </label>

                    <div className={styles.formActions}>
                        <button type="submit" className={styles.submitButton} disabled={clubRequestSubmitting}>
                            {clubRequestSubmitting
                                ? texts?.submitting || "Submitting..."
                                : texts?.submit_club_request || "Submit Club Request"}
                        </button>
                    </div>
                </form>

                {clubRequestMessage.text ? (
                    <p className={`${styles.notice} ${clubRequestMessage.type === "error" ? styles.noticeError : styles.noticeSuccess}`}>
                        {clubRequestMessage.text}
                    </p>
                ) : null}
            </article>

            {/* Right Column: Both types of requests */}
            <div className={styles.requestsSidebar}>
                <article className={styles.panel}>
                    <div className={styles.panelTopRow}>
                        <h3 className={styles.panelTitle}>
                            {texts?.my_club_registration_requests || "My Club Registration Requests"}
                        </h3>
                        <span className={styles.counter}>{clubCreationRequests.length}</span>
                    </div>

                    {clubCreationRequests.length === 0 ? (
                        <p className={styles.muted}>
                            {texts?.no_club_registration_requests_yet || "No club registration requests yet."}
                        </p>
                    ) : (
                        <ul className={styles.list}>
                            {clubCreationRequests.map((request) => (
                                <li className={styles.listItem} key={request.id}>
                                    <div>
                                        <p className={styles.primaryText}>{request.name || texts?.new_club || "New Club"}</p>
                                        <p className={styles.secondaryText}>
                                            {request.city || texts?.unknown_city || "Unknown city"}
                                            {request.sport ? ` • ${request.sport}` : ""}
                                        </p>
                                    </div>
                                    <span className={`${styles.statusPill} ${statusClass(request.status)}`}>
                                        {statusLabel(request.status, texts)}
                                    </span>
                                </li>
                            ))}
                        </ul>
                    )}
                </article>
            </div>
        </section>
    );
}

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
        <div className={`${styles.tabContent} ${styles.contentFade}`}>
            <h2 className={styles.panelTitle}>{texts?.manage_clubs_title || "Club Administration"}</h2>
            
            <div className={styles.twoColumnLayout}>
                <section className={styles.mainColumn}>
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
                                                {club.city} - {club.sport}
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

                <aside className={styles.requestsSidebar}>
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
                                                const row = e.currentTarget.closest(`.${styles.actionRow}`);
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
                                                const row = e.currentTarget.closest(`.${styles.actionRow}`);
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

const SORT_OPTIONS      = [{ value: "id", label: "By ID" }, { value: "name", label: "By Name" }];
const PAGE_SIZE_OPTIONS = [6, 12, 24];

export function TeamsTab({
                             teams, total, loading, error,
                             sort, pageSize, hasMore,
                             onLoad, onLoadMore,
                             texts,
                             currentUser,
                         }) {
    const navigate = useNavigate();

    useEffect(() => { void onLoad(); }, []); // eslint-disable-line react-hooks/exhaustive-deps

    function handleTeamCreated() {
        void onLoad({ sort, pageSize });
    }

    return (
        <article className={`${styles.panel} ${styles.contentFade}`} style={{ display: "grid", gap: "1rem" }}>

            {/* Header row */}
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "0.75rem" }}>
                <h3 className={styles.panelTitle} style={{ margin: 0 }}>
                    {texts?.my_teams || "My Teams"}
                    {total !== null && (
                        <span className={styles.counter} style={{ marginLeft: "0.6rem" }}>{total}</span>
                    )}
                </h3>

                <div style={{ display: "flex", alignItems: "center", gap: "0.6rem", flexWrap: "wrap" }}>
                    <select
                        className={styles.searchInput}
                        style={{ width: "auto", marginBottom: 0 }}
                        value={sort}
                        onChange={e => void onLoad({ sort: e.target.value, pageSize })}
                        disabled={loading}
                    >
                        {SORT_OPTIONS.map(o => (
                            <option key={o.value} value={o.value}>{o.label}</option>
                        ))}
                    </select>

                    <select
                        className={styles.searchInput}
                        style={{ width: "auto", marginBottom: 0 }}
                        value={pageSize}
                        onChange={e => void onLoad({ sort, pageSize: Number(e.target.value) })}
                        disabled={loading}
                    >
                        {PAGE_SIZE_OPTIONS.map(n => (
                            <option key={n} value={n}>{n} per load</option>
                        ))}
                    </select>

                    <CreateTeamButton onCreated={handleTeamCreated} />
                </div>
            </div>

            {/* Error */}
            {error && <p className={styles.warning}>{error}</p>}

            {/* Empty state */}
            {!loading && !error && teams.length === 0 && (
                <p className={styles.muted}>
                    {texts?.no_teams_yet || "You are not a member of any team yet."}
                </p>
            )}

            {/* Teams list */}
            {teams.length > 0 && (
                <ul className={styles.list} style={{ margin: 0, padding: 0 }}>
                    {teams.map(team => (
                        <TeamCard key={team.id} team={team} texts={texts} currentUser={currentUser} />
                    ))}
                </ul>
            )}

            {/* Loading */}
            {loading && (
                <p className={styles.muted}>{texts?.loading_teams || "Loading teams…"}</p>
            )}

            {/* Load more */}
            {!loading && hasMore && teams.length > 0 && (
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                    <span className={styles.muted} style={{ fontSize: "0.82rem" }}>
                        {texts?.showing || "Showing"} {teams.length}{total !== null ? ` / ${total}` : ""}
                    </span>
                    <button className={styles.primaryButton} onClick={() => void onLoadMore()}>
                        {texts?.load_more || "Load more"}
                    </button>
                </div>
            )}
        </article>
    );
}
 
export function AvailabilityTab({
    availabilityBlocks,
    availabilityForm,
    availabilityLoading,
    availabilitySubmitting,
    availabilityMessage,
    onAvailabilityFieldChange,
    onAvailabilitySubmit,
    onAvailabilityDelete,
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
                            {texts?.date || "Date"}
                            <input
                                className={styles.formInput}
                                type="date"
                                name="date"
                                value={availabilityForm.date}
                                onChange={onAvailabilityFieldChange}
                                required
                            />
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
                                : texts?.add_availability_block ||
                                  "Add availability block"}
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

            <article className={styles.panel}>
                <div className={styles.panelTopRow}>
                    <h3 className={styles.panelTitle}>
                        {texts?.availability_blocks || "Your blocks"}
                    </h3>
                    <span className={styles.counter}>
                        {availabilityBlocks.length}
                    </span>
                </div>

                {availabilityLoading ? (
                    <p className={styles.muted}>
                        {texts?.loading || "Loading..."}
                    </p>
                ) : null}

                {!availabilityLoading && availabilityBlocks.length === 0 ? (
                    <p className={styles.muted}>
                        {texts?.no_availability_blocks ||
                            "No availability blocks yet."}
                    </p>
                ) : null}

                {!availabilityLoading && availabilityBlocks.length > 0 ? (
                    <ul className={styles.list}>
                        {availabilityBlocks.map((block) => (
                            <li className={styles.listItem} key={block.id}>
                                <div>
                                    <p className={styles.primaryText}>
                                        {formatLocalTimestamp(block.start_at)} -{" "}
                                        {formatLocalTimestamp(block.end_at)}
                                    </p>
                                </div>
                                <button
                                    className={styles.primaryButton}
                                    type="button"
                                    onClick={() =>
                                        onAvailabilityDelete(block.id)
                                    }
                                >
                                    {texts?.delete || "Delete"}
                                </button>
                            </li>
                        ))}
                    </ul>
                ) : null}
            </article>
        </section>
    )
}

// Achievements Tab

const ACHIEVEMENT_DEFINITIONS = [
    {
        id: "first_steps",
        icon: "★",
        name: "First Steps",
        description: "Created your account",
        check: () => true,
    },
    {
        id: "club_member",
        icon: "⬡",
        name: "Club Member",
        description: "Joined your first club",
        check: ({ myClubs }) => myClubs.length >= 1,
    },
    {
        id: "social_butterfly",
        icon: "◈",
        name: "Social Butterfly",
        description: "Member of 3 or more clubs",
        check: ({ myClubs }) => myClubs.length >= 3,
    },
    {
        id: "team_player",
        icon: "▲",
        name: "Team Player",
        description: "Part of your first team",
        check: ({ teams }) => teams.length >= 1,
    },
    {
        id: "squad_goals",
        icon: "◆",
        name: "Squad Goals",
        description: "Part of 3 or more teams",
        check: ({ teams }) => teams.length >= 3,
    },
    {
        id: "trailblazer",
        icon: "→",
        name: "Trailblazer",
        description: "Submitted your first join request",
        check: ({ myRequests }) => myRequests.length >= 1,
    },
    {
        id: "networker",
        icon: "⬟",
        name: "Networker",
        description: "Submitted 5 or more join requests",
        check: ({ myRequests }) => myRequests.length >= 5,
    },
    {
        id: "club_leader",
        icon: "♛",
        name: "Club Leader",
        description: "Own and manage a club",
        check: ({ isClubOwner }) => isClubOwner,
    },
    {
        id: "first_victory",
        icon: "✦",
        name: "First Victory",
        description: "Won your first match",
        check: ({ wins }) => wins >= 1,
    },
    {
        id: "hat_trick",
        icon: "◉",
        name: "Hat Trick",
        description: "Won 3 or more matches",
        check: ({ wins }) => wins >= 3,
    },
    {
        id: "champion",
        icon: "♔",
        name: "Champion",
        description: "Won 10 or more matches",
        check: ({ wins }) => wins >= 10,
    },
    {
        id: "on_fire",
        icon: "↑",
        name: "On Fire",
        description: "Won 3 matches in a row",
        check: ({ currentStreak }) => currentStreak >= 3,
    },
    {
        id: "unstoppable",
        icon: "⬆",
        name: "Unstoppable",
        description: "Best win streak of 5 or more",
        check: ({ bestStreak }) => bestStreak >= 5,
    },
]

const EMPTY_STATS = { wins: 0, current_streak: 0, best_streak: 0, total_matches: 0 }

export function AchievementsTab({ myClubs, myRequests, teams, isClubOwner, texts }) {
    const [stats, setStats] = useState(EMPTY_STATS)
    const [statsLoading, setStatsLoading] = useState(true)

    useEffect(() => {
        fetch("/api/me/achievements", { credentials: "include" })
            .then((res) => res.ok ? res.json() : EMPTY_STATS)
            .then((data) => setStats(data))
            .catch(() => setStats(EMPTY_STATS))
            .finally(() => setStatsLoading(false))
    }, [])

    const ctx = {
        myClubs,
        myRequests,
        teams,
        isClubOwner,
        wins: stats.wins,
        currentStreak: stats.current_streak,
        bestStreak: stats.best_streak,
    }

    const achievements = useMemo(
        () => ACHIEVEMENT_DEFINITIONS.map((def) => ({ ...def, unlocked: def.check(ctx) })),
        [myClubs.length, myRequests.length, teams.length, isClubOwner, stats],
    )

    const unlockedCount = achievements.filter((a) => a.unlocked).length
    const winRate = stats.total_matches > 0
        ? Math.round((stats.wins / stats.total_matches) * 100)
        : 0

    return (
        <div className={`${styles.contentGrid} ${styles.contentFade}`}>
            <article className={styles.panel}>
                <h3 className={styles.panelTitle}>{texts?.match_stats || "Match Stats"}</h3>
                {statsLoading ? (
                    <p className={styles.muted}>{texts?.loading || "Loading..."}</p>
                ) : (
                    <div className={styles.metrics}>
                        <div className={styles.metricCard}>
                            <p className={styles.metricLabel}>{texts?.total_wins || "Total Wins"}</p>
                            <p className={styles.metricValue}>{stats.wins}</p>
                        </div>
                        <div className={styles.metricCard}>
                            <p className={styles.metricLabel}>{texts?.total_matches || "Matches Played"}</p>
                            <p className={styles.metricValue}>{stats.total_matches}</p>
                        </div>
                        <div className={styles.metricCard}>
                            <p className={styles.metricLabel}>{texts?.win_rate || "Win Rate"}</p>
                            <p className={styles.metricValue}>{winRate}%</p>
                        </div>
                        <div className={styles.metricCard}>
                            <p className={styles.metricLabel}>{texts?.current_streak || "Current Streak"}</p>
                            <p className={styles.metricValue}>{stats.current_streak}</p>
                        </div>
                        <div className={styles.metricCard}>
                            <p className={styles.metricLabel}>{texts?.best_streak || "Best Streak"}</p>
                            <p className={styles.metricValue}>{stats.best_streak}</p>
                        </div>
                    </div>
                )}
            </article>

            <article className={`${styles.panel}`}>
                <div className={styles.panelTopRow}>
                    <h3 className={styles.panelTitle}>{texts?.achievements || "Achievements"}</h3>
                    <span className={styles.counter}>{unlockedCount} / {achievements.length}</span>
                </div>
                <p className={styles.muted} style={{ marginBottom: "1rem" }}>
                    {texts?.achievements_subtitle || "Milestones you have reached on your journey."}
                </p>
                <div className={dashboardStyles.achievementGrid}>
                    {achievements.map((achievement) => (
                        <div
                            key={achievement.id}
                            className={`${dashboardStyles.achievementCard} ${
                                achievement.unlocked
                                    ? dashboardStyles.achievementCardUnlocked
                                    : dashboardStyles.achievementCardLocked
                            }`}
                        >
                            <span className={dashboardStyles.achievementIcon}>{achievement.icon}</span>
                            <p className={dashboardStyles.achievementName}>{achievement.name}</p>
                            <p className={dashboardStyles.achievementDesc}>{achievement.description}</p>
                            <span
                                className={`${dashboardStyles.achievementBadge} ${
                                    achievement.unlocked
                                        ? dashboardStyles.achievementBadgeUnlocked
                                        : dashboardStyles.achievementBadgeLocked
                                }`}
                            >
                                {achievement.unlocked
                                    ? (texts?.unlocked || "Unlocked")
                                    : (texts?.locked || "Locked")}
                            </span>
                        </div>
                    ))}
                </div>
            </article>
        </div>
    )
}
