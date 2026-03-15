import { Link } from "react-router-dom";
import styles from "@/style/Dashboard.module.css";
import { statusClass, statusLabel } from "@/app/components/dashboard/dashboardUtils.js";

export function OverviewTab({ myClubs, myRequests, pendingJoinRequestClubIds, clubCreationRequests }) {
    return (
        <div className={`${styles.contentGrid} ${styles.contentFade}`}>
            <article className={styles.panel}>
                <h3 className={styles.panelTitle}>My Clubs</h3>

                {myClubs.length === 0 ? (
                    <p className={styles.muted}>You are not a member of any club yet.</p>
                ) : (
                    <ul className={styles.list}>
                        {myClubs.map((club) => {
                            const clubId = club?.id ?? club?.club_id;
                            return (
                                <li className={styles.listItem} key={clubId}>
                                    <div>
                                        <p className={styles.primaryText}>{club?.name || `Club #${clubId}`}</p>
                                        <p className={styles.secondaryText}>
                                            {(club?.membership_status || "member").toString()}
                                        </p>
                                    </div>
                                    <Link className={styles.linkButton} to={`/clubs/${clubId}`}>
                                        Open
                                    </Link>
                                </li>
                            );
                        })}
                    </ul>
                )}
            </article>

            <article className={styles.panel}>
                <h3 className={styles.panelTitle}>Quick Highlights</h3>
                <div className={styles.metrics}>
                    <div className={styles.metricCard}>
                        <p className={styles.metricLabel}>Join requests</p>
                        <p className={styles.metricValue}>{myRequests.length}</p>
                    </div>
                    <div className={styles.metricCard}>
                        <p className={styles.metricLabel}>Pending join requests</p>
                        <p className={styles.metricValue}>{pendingJoinRequestClubIds.size}</p>
                    </div>
                    <div className={styles.metricCard}>
                        <p className={styles.metricLabel}>Club registration requests</p>
                        <p className={styles.metricValue}>{clubCreationRequests.length}</p>
                    </div>
                </div>
            </article>
        </div>
    );
}

export function SearchTab({
    searchTerm,
    onSearchChange,
    discoverLoading,
    discoverError,
    filteredDiscoverClubs,
    myClubIds,
    pendingJoinRequestClubIds,
}) {
    return (
        <article className={`${styles.panel} ${styles.contentFade}`}>
            <div className={styles.panelTopRow}>
                <h3 className={styles.panelTitle}>Search Clubs</h3>
                <span className={styles.counter}>{filteredDiscoverClubs.length}</span>
            </div>

            <input
                className={styles.searchInput}
                type="search"
                value={searchTerm}
                onChange={(event) => onSearchChange(event.target.value)}
                placeholder="Search by club name"
                aria-label="Search clubs"
            />

            {discoverLoading ? <p className={styles.muted}>Clubs laden...</p> : null}
            {discoverError ? <p className={styles.warning}>{discoverError}</p> : null}

            {!discoverLoading && !discoverError ? (
                filteredDiscoverClubs.length === 0 ? (
                    <p className={styles.muted}>No clubs found.</p>
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
                                            <span className={`${styles.statusPill} ${styles.statusApproved}`}>Joined</span>
                                        ) : null}

                                        {!isJoined && hasPendingRequest ? (
                                            <span className={`${styles.statusPill} ${styles.statusPending}`}>Pending</span>
                                        ) : null}

                                        {!isJoined && !hasPendingRequest ? (
                                            <button className={styles.primaryButton} type="button" disabled>
                                                Request to Join
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

export function RequestsTab({ myRequests }) {
    return (
        <article className={`${styles.panel} ${styles.contentFade}`}>
            <div className={styles.panelTopRow}>
                <h3 className={styles.panelTitle}>My Join Requests</h3>
                <span className={styles.counter}>{myRequests.length}</span>
            </div>

            {myRequests.length === 0 ? (
                <p className={styles.muted}>No join requests yet.</p>
            ) : (
                <ul className={styles.list}>
                    {myRequests.map((request) => {
                        const requestId = request?.id ?? `${request?.club_id}-${request?.status}`;
                        const requestState = request?.status || "pending";

                        return (
                            <li key={requestId} className={styles.listItem}>
                                <div>
                                    <p className={styles.primaryText}>
                                        {request?.club_name || request?.club?.name || "Unknown club"}
                                    </p>
                                    <p className={styles.secondaryText}>Requested: {request?.requested_at || "-"}</p>
                                </div>

                                <span className={`${styles.statusPill} ${statusClass(requestState)}`}>
                                    {statusLabel(requestState)}
                                </span>
                            </li>
                        );
                    })}
                </ul>
            )}
        </article>
    );
}

export function CreateClubTab({
    clubRequestForm,
    clubRequestSubmitting,
    clubRequestMessage,
    clubCreationRequests,
    onFieldChange,
    onSubmit,
}) {
    return (
        <section className={`${styles.createClubLayout} ${styles.contentFade}`}>
            <article className={styles.panel}>
                <h3 className={styles.panelTitle}>Request Your Own Club</h3>
                <form className={styles.form} onSubmit={onSubmit}>
                    <label className={styles.formLabel}>
                        Club Name
                        <input
                            className={styles.formInput}
                            type="text"
                            name="name"
                            value={clubRequestForm.name}
                            onChange={onFieldChange}
                            placeholder="What is your club's name?"
                            required
                        />
                    </label>

                    <div className={styles.formRow}>
                        <label className={styles.formLabel}>
                            City
                            <input
                                className={styles.formInput}
                                type="text"
                                name="city"
                                value={clubRequestForm.city}
                                onChange={onFieldChange}
                                placeholder="City where your club is based"
                                required
                            />
                        </label>

                        <label className={styles.formLabel}>
                            Main Sport
                            <input
                                className={styles.formInput}
                                type="text"
                                name="sport"
                                value={clubRequestForm.sport}
                                onChange={onFieldChange}
                                placeholder="Padel"
                                required
                            />
                        </label>
                    </div>

                    <label className={styles.formLabel}>
                        Description
                        <textarea
                            className={styles.formTextarea}
                            name="description"
                            value={clubRequestForm.description}
                            onChange={onFieldChange}
                            placeholder="Tell us what your club is about and why you want to use our platform"
                            rows={4}
                            required
                        />
                    </label>

                    <div className={styles.formActions}>
                        <button type="submit" className={styles.submitButton} disabled={clubRequestSubmitting}>
                            {clubRequestSubmitting ? "Submitting..." : "Submit Club Request"}
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
                    <h3 className={styles.panelTitle}>My Club Registration Requests</h3>
                    <span className={styles.counter}>{clubCreationRequests.length}</span>
                </div>

                {clubCreationRequests.length === 0 ? (
                    <p className={styles.muted}>No club registration requests yet.</p>
                ) : (
                    <ul className={styles.list}>
                        {clubCreationRequests.map((request) => (
                            <li className={styles.listItem} key={request.id}>
                                <div>
                                    <p className={styles.primaryText}>{request.name || "New Club"}</p>
                                    <p className={styles.secondaryText}>
                                        {request.city || "Unknown city"}
                                        {request.sport ? ` • ${request.sport}` : ""}
                                    </p>
                                </div>
                                <span className={`${styles.statusPill} ${statusClass(request.status)}`}>
                                    {statusLabel(request.status)}
                                </span>
                            </li>
                        ))}
                    </ul>
                )}
            </article>
        </section>
    );
}
