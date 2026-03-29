import { useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import commonStyles from "@/style/common/Common.module.css";
import dashStyles from "@/style/Dashboard.module.css";

import TeamCard from "@/components/dashboard/TeamCard.jsx";
import {statusClass, statusLabel} from "@/components/dashboard/dashboardUtils.js";
import CreateTeamButton from "@/components/team/CreateTeamButton.jsx";


// We combine both modules into one proxy object,
// so as not to rewrite every styles.* in the template.
// Dashboard-specific classes (shell, sidebar, …) only cover what
// is not in Common, so there are no collisions.
const styles = { ...commonStyles, ...dashStyles };

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
                                            (club?.membership_status || texts?.member_status || "member").toString()
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
                                            <button className={styles.primaryButton} type="button" disabled>
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

//  Requests Tab 

export function RequestsTab({ myRequests, texts }) {
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
                              }) {
    return (
        <section className={`${styles.createClubLayout} ${styles.contentFade}`}>
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
                    <p
                        className={`${styles.notice} ${
                            clubRequestMessage.type === "error"
                                ? styles.noticeError
                                : clubRequestMessage.type === "success"
                                    ? styles.noticeSuccess
                                    : styles.noticeInfo
                        }`}
                    >
                        {clubRequestMessage.text}
                    </p>
                ) : null}
            </article>

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
        </section>
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
 