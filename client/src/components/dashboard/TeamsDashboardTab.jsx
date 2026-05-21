// Dashboard UI component for TeamsDashboardTab.

import commonStyles     from "@/style/common/Common.module.css";
import animationStyles  from "@/style/common/Animation.module.css";
import panelStyles      from "@/style/common/Panel.module.css";
import formStyles       from "@/style/common/Forms.module.css";
import buttonStyles     from "@/style/common/Buttons.module.css";
import dashboardStyles  from "@/style/dashboard/Dashboard.module.css";

import TeamCard             from "@/components/dashboard/TeamCard.jsx";
import CreateTeamButton     from "@/components/team/CreateTeamButton.jsx";
import TeamInvitations      from "@/components/team/TeamInvitations.jsx";


import { useCurrentUserContext }    from "@/context/useCurrentUserContext.jsx";
import { useMyTeams }   from "@/hooks/dashboard/useMyTeams.js";
import { useMyClubs }   from "@/hooks/useMyClubs.js";


const PAGE_SIZE_OPTIONS = [6, 12, 24];

/**
 * TeamsTab
 *
 * Dashboard tab that lists all teams the current account is involved with
 * and provides two action buttons:
 *
 *   CreateTeamButton  - existing flow to create a new team
 *
 * managedTeams (teams from /api/teams/my) are fetched here so that
 */
export function TeamsTab({ texts, theme, onInvitationsChanged }) {
    /*
     Owns the dashboard tab that lists the current account's teams.
    */
    const { currentUser } = useCurrentUserContext();

    // All teams the account is involved with (my-all) — shown in the list
    const {
        teams,
        total,
        loading,
        error,
        sort,
        pageSize,
        hasMore,
        load,
        loadMore,
    } = useMyTeams();

    const { clubs: myClubs } = useMyClubs();

    function handleTeamCreated() {
        /*
         Reloads the team list after a team is created.
        */
        void load({ sort, pageSize });
    }

    function handleInvitationsResolved() {
        /*
         Keeps the invitation count and the team list in sync after a response.
        */
        void load({ sort, pageSize });
        void onInvitationsChanged?.();
    }
    return (
        <div className={`${animationStyles.contentGrid} ${animationStyles.contentFade}`}>


            {/* My Teams Section */}
            <article className={`${panelStyles.panel}`} style={{ gridColumn: "1 / -1" }}>

                {/* Header row */}
                <div className={dashboardStyles.dashboardSectionHeader}>
                    <h3 className={panelStyles.panelTitle} style={{ margin: 0 }}>
                        {/* The counter helps show how many teams the current user can reach from this tab. */}
                        {texts?.my_teams || "My Teams"}
                        {total !== null && (
                            <span
                                className={panelStyles.panelCounter}
                                style={{ marginLeft: "0.6rem" }}
                            >
                                {total}
                            </span>
                        )}
                    </h3>

                    <div className={dashboardStyles.dashboardControlGroup}>
                        {/* Sort selector keeps the list order predictable when the dataset gets large. */}
                        <select
                            className={`${formStyles.searchInput} ${dashboardStyles.dashboardSelect}`}
                            value={sort}
                            onChange={e => void load({ sort: e.target.value, pageSize })}
                            disabled={loading}
                        >
                            {[
                                { value: "id",   label: texts?.sort_id   || "By ID"   },
                                { value: "name", label: texts?.sort_name || "By name" },
                            ].map(o => (
                                <option key={o.value} value={o.value}>{o.label}</option>
                            ))}
                        </select>

                        {/* Page size selector controls how many rows the tab loads at once. */}
                        <select
                            className={`${formStyles.searchInput} ${dashboardStyles.dashboardSelect}`}
                            value={pageSize}
                            onChange={e => void load({ sort, pageSize: Number(e.target.value) })}
                            disabled={loading}
                        >
                            {PAGE_SIZE_OPTIONS.map(n => (
                                <option key={n} value={n}>
                                    {n} {texts?.per_page || "per page"}
                                </option>
                            ))}
                        </select>

                        {/* The create-team action stays in the same toolbar as sorting and paging. */}
                        <CreateTeamButton
                            clubs={myClubs}
                            onCreated={handleTeamCreated}
                            theme={theme}
                            texts={texts}
                        />


                    </div>
                </div>

                {/* Error */}
                {error && <p className={commonStyles.warning}>{error}</p>}

                {/* Empty state */}
                {!loading && !error && teams.length === 0 && (
                    <p className={commonStyles.muted}>
                        {texts?.no_teams_yet || "Je bent nog geen lid van een team."}
                    </p>
                )}

                {/* Teams list */}
                {teams.length > 0 && (
                    <ul className={panelStyles.list} style={{ margin: 0, padding: 0 }}>
                        {teams.map(team => (
                            // Reuse the shared team card so actions and theme styling stay consistent.
                            <TeamCard
                                key={team.id}
                                team={team}
                                texts={texts}
                                currentUser={currentUser}
                                theme={theme}
                            />
                        ))}
                    </ul>
                )}

                {/* Loading indicator */}
                {loading && (
                    <p className={commonStyles.muted}>
                        {texts?.loading_teams || "Teams laden..."}
                    </p>
                )}

                {/* Load more */}
                {!loading && hasMore && teams.length > 0 && (
                    <div className={dashboardStyles.dashboardFooterRow}>
                        <span className={commonStyles.muted} style={{ fontSize: "0.82rem" }}>
                            {texts?.showing || "Weergegeven"} {teams.length}
                            {total !== null ? ` / ${total}` : ""}
                        </span>
                        <button
                            className={buttonStyles.primaryButton}
                            onClick={() => void loadMore()}
                        >
                            {texts?.load_more || "Meer laden"}
                        </button>
                    </div>
                )}
            </article>

            {/* Team Invitations Section */}
            <div style={{ gridColumn: "1 / -1" }}>
                <TeamInvitations onResolved={handleInvitationsResolved} />
            </div>
        </div>
    );
}
