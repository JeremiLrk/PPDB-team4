import { useNavigate, useParams, Link } from "react-router-dom";
import { useState } from "react";

import { useTeam }           from "@/hooks/teams/useTeam.js";
import { useTeamPlayers }    from "@/hooks/teams/useTeamPlayers.js";
import { useTeamManagers }   from "@/hooks/teams/useTeamManagers.js";
import { useCurrentUserContext } from "@/context/useCurrentUserContext.jsx";
import { useLangContext } from "@/context/useLangContext.jsx";
import { usePageTexts } from "@/hooks/common/usePageTexts.js";

import AddPlayerButton   from "@/components/team/AddPlayerButton.jsx";
import AddManagerButton  from "@/components/team/AddManagerButton.jsx";
import PlayerCard        from "@/components/team/PlayerCard.jsx";
import ManagerCard       from "@/components/team/ManagerCard.jsx";
import RenameTeamButton  from "@/components/team/RenameTeamButton.jsx";
import GearIcon          from "@/components/icon/GearIcon.jsx";
import { canManageTeam } from "@/components/team/TeamSettingsLink.jsx";

import styles       from "@/style/TeamSettings.module.css";
import commonStyles from "@/style/common/Common.module.css";
import panelStyles  from "@/style/common/Panel.module.css";

/**
 * Check can_edit_managers on the frontend.
 * Mirrors _can_edit_managers() on the server.
 * Administrator / ClubOwner — always true.
 * TeamManager — via managerPermissions or managedTeamIds as a fallback.
 */
function userCanEditManagers(account, team) {
    if (!account || !team) return false;
    const roles = account.roles ?? [];
    if (roles.includes("administrator")) return true;
    if (roles.includes("club_owner")) {
        return (team.clubId && account.clubIds?.includes(team.clubId))
            || account.managedTeamIds?.includes(team.id);
    }
    if (roles.includes("team_manager")) {
        const perms = account.managerPermissions?.[team.id];
        if (perms !== undefined) return perms.canEditManagers;
        return account.managedTeamIds?.includes(team.id) ?? false;
    }
    return false;
}

export default function TeamSettings() {
    const { teamId }      = useParams();
    const { currentUser } = useCurrentUserContext();
    const { lang } = useLangContext();
    const navigate        = useNavigate();
    const texts = usePageTexts("team_settings", lang);

    const { team,    loading: teamLoading,    error: teamError    } = useTeam(teamId);
    const { players, loading: playersLoading, error: playersError,
        total:   playersTotal, reload: reloadPlayers }           = useTeamPlayers(teamId);
    const { managers, loading: managersLoading, error: managersError,
        total:   managersTotal, reload: reloadManagers }         = useTeamManagers(teamId);

    const [displayName, setDisplayName] = useState(null);
    const teamName = displayName ?? team?.name ?? "";

    /*  loading  */
    if (teamLoading) {
        return (
            <div className={styles.state}>
                <div className={styles.spinner} />
                <span>{texts.loading_team || "Team loading..."}</span>
            </div>
        );
    }

    /*  fetch error  */
    if (teamError) {
        return (
            <div className={styles.state}>
                <p className={styles.error}>{teamError}</p>
                <button className={styles.backBtn} onClick={() => navigate("/teams")}>
                    &lt;- {texts.back_to_teams || "Back to teams"}
                </button>
            </div>
        );
    }

    if (!team) return null;

    /*  access check  */
    if (!currentUser) {
        return (
            <div className={styles.state}>
                <p className={styles.error}>{texts.login_required || "You must be logged in to open this page."}</p>
                <Link to="/login" className={styles.backBtn}>→ {texts.login_button || "Log in"}</Link>
            </div>
        );
    }

    if (!canManageTeam(currentUser, team)) {
        return (
            <div className={styles.state}>
                <p className={styles.error}>
                    {texts.access_denied || "Access denied. You do not have permission to manage this team."}
                </p>
                <button className={styles.backBtn} onClick={() => navigate(`/teams/${teamId}`)}>
                    &lt;- {texts.back_to_team || "Back to team"}
                </button>
            </div>
        );
    }

    const canDeleteManagers = userCanEditManagers(currentUser, team);

    /*  main page  */
    return (
        <section className={styles.page}>

            {/* Navigation */}
            <div className={styles.breadcrumbs}>
                <button className={styles.backBtn} onClick={() => navigate(`/teams/${teamId}`)}>
                    &lt;- {teamName}
                </button>
                <span className={styles.breadcrumbSep}>/</span>
                <span className={styles.breadcrumbCurrent}>{texts.breadcrumb_settings || "Settings"}</span>
            </div>

            {/* Hero */}
            <div className={styles.hero}>
                <div className={styles.heroAccent} />
                <div className={styles.heroBody}>
                    <div className={styles.heroTop}>
                        <div>
                            <div className={styles.nameRow}>
                                <h1 className={styles.name}>{teamName}</h1>
                                <RenameTeamButton
                                    teamId={teamId}
                                    currentName={teamName}
                                    onRenamed={t => setDisplayName(t.name)}
                                />
                            </div>
                            <div className={styles.tags}>
                                <Tag label={texts.settings_title || "Team settings"} accent />
                                <Tag
                                    label={team.clubName ? team.clubName : (texts.independent_team || "Independent")}
                                    muted={!team.clubId}
                                />
                                <Tag label={team.sportName ? team.sportName  : "No sport"}    muted={!team.sportTypeId} />

                            </div>
                        </div>
                        <GearIcon size={32} title={texts.settings_title || "Team settings"} className={styles.settingsIcon} />
                    </div>
                </div>
            </div>

            {/*  Managers section  */}
            <div className={styles.section}>
                <div className={styles.sectionHeader}>
                    <div className={styles.sectionTitleRow}>
                        <h2 className={styles.sectionTitle}>{texts.managers_title || "Managers"}</h2>
                        {managersTotal !== null && (
                            <span className={panelStyles.panelCounter}>{managersTotal}</span>
                        )}
                    </div>
                    <AddManagerButton
                        teamId={teamId}
                        team={team}
                        onAdded={reloadManagers}
                    />
                </div>

                {managersLoading && (
                    <div className={styles.inlineState}>
                        <div className={styles.spinner} />
                        <span>{texts.loading_managers || "Managers loading..."}</span>
                    </div>
                )}

                {!managersLoading && managersError && (
                    <div className={styles.inlineState}>
                        <p className={styles.error}>{managersError}</p>
                        <button className={styles.retryBtn} onClick={reloadManagers}>{texts.retry || "Retry"}</button>
                    </div>
                )}

                {!managersLoading && !managersError && managers.length === 0 && (
                    <p className={commonStyles.muted}>{texts.no_managers || "No managers in this team yet."}</p>
                )}

                {!managersLoading && !managersError && managers.length > 0 && (
                    <ul className={panelStyles.list}>
                        {managers.map(manager => (
                            <ManagerCard
                                key={manager.id}
                                manager={manager}
                                teamId={teamId}
                                canDelete={canDeleteManagers}
                                onDeleted={reloadManagers}
                            />
                        ))}
                    </ul>
                )}
            </div>

            {/*  Players section  */}
            <div className={styles.section}>
                <div className={styles.sectionHeader}>
                    <div className={styles.sectionTitleRow}>
                        <h2 className={styles.sectionTitle}>{texts.players_title || "Players"}</h2>
                        {playersTotal !== null && (
                            <span className={panelStyles.panelCounter}>{playersTotal}</span>
                        )}
                    </div>
                    <AddPlayerButton teamId={teamId} onAdded={reloadPlayers} />
                </div>

                {playersLoading && (
                    <div className={styles.inlineState}>
                        <div className={styles.spinner} />
                        <span>{texts.loading_players || "Players loading..."}</span>
                    </div>
                )}

                {!playersLoading && playersError && (
                    <div className={styles.inlineState}>
                        <p className={styles.error}>{playersError}</p>
                        <button className={styles.retryBtn} onClick={reloadPlayers}>{texts.retry || "Retry"}</button>
                    </div>
                )}

                {!playersLoading && !playersError && players.length === 0 && (
                    <p className={commonStyles.muted}>{texts.no_players || "No players in this team yet. Add one above."}</p>
                )}

                {!playersLoading && !playersError && players.length > 0 && (
                    <ul className={panelStyles.list}>
                        {players.map(player => (
                            <PlayerCard
                                key={player.playerId ?? player.id}
                                player={player}
                                teamId={teamId}
                                onDeleted={reloadPlayers}
                            />
                        ))}
                    </ul>
                )}
            </div>

        </section>
    );
}

/*  Local sub-components  */

function Tag({ label, muted, accent }) {
    const cls = [
        styles.tag,
        muted  ? styles.tagMuted  : "",
        accent ? styles.tagAccent : "",
    ].filter(Boolean).join(" ");
    return <span className={cls}>{label}</span>;
}