import { useNavigate, useParams, Link } from "react-router-dom";
import { useState } from "react";

import { useTeam }           from "@/hooks/teams/useTeam.js";
import { useTeamPlayers }    from "@/hooks/teams/useTeamPlayers.js";
import { useTeamManagers }   from "@/hooks/teams/useTeamManagers.js";
import { useCurrentUserContext } from "@/context/useCurrentUserContext.jsx";

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
 * Перевірка can_edit_managers на фронтенді.
 * Відзеркалює _can_edit_managers() на сервері.
 * Administrator / ClubOwner — завжди true.
 * TeamManager — через managerPermissions або managedTeamIds як fallback.
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
    const navigate        = useNavigate();

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
                <span>Team laden…</span>
            </div>
        );
    }

    /*  fetch error  */
    if (teamError) {
        return (
            <div className={styles.state}>
                <p className={styles.error}>{teamError}</p>
                <button className={styles.backBtn} onClick={() => navigate("/teams")}>
                    &lt;- Terug naar teams
                </button>
            </div>
        );
    }

    if (!team) return null;

    /*  access check  */
    if (!currentUser) {
        return (
            <div className={styles.state}>
                <p className={styles.error}>Je moet ingelogd zijn om deze pagina te openen.</p>
                <Link to="/login" className={styles.backBtn}>→ Inloggen</Link>
            </div>
        );
    }

    if (!canManageTeam(currentUser, team)) {
        return (
            <div className={styles.state}>
                <p className={styles.error}>
                    Toegang geweigerd. Je hebt geen rechten om dit team te beheren.
                </p>
                <button className={styles.backBtn} onClick={() => navigate(`/teams/${teamId}`)}>
                    &lt;- Terug naar team
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
                <span className={styles.breadcrumbCurrent}>Instellingen</span>
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
                                <Tag label="Instellingen" accent />
                                <Tag label={team.clubId ? `Club #${team.clubId}` : "Onafhankelijk"} muted={!team.clubId} />
                                <Tag label={`ID: ${team.id}`} muted />
                            </div>
                        </div>
                        <GearIcon size={32} title="Teaminstellingen" className={styles.settingsIcon} />
                    </div>
                </div>
            </div>

            {/*  Managers section  */}
            <div className={styles.section}>
                <div className={styles.sectionHeader}>
                    <div className={styles.sectionTitleRow}>
                        <h2 className={styles.sectionTitle}>Beheerders</h2>
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
                        <span>Beheerders laden…</span>
                    </div>
                )}

                {!managersLoading && managersError && (
                    <div className={styles.inlineState}>
                        <p className={styles.error}>{managersError}</p>
                        <button className={styles.retryBtn} onClick={reloadManagers}>Opnieuw proberen</button>
                    </div>
                )}

                {!managersLoading && !managersError && managers.length === 0 && (
                    <p className={commonStyles.muted}>Nog geen beheerders in dit team.</p>
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
                        <h2 className={styles.sectionTitle}>Spelers</h2>
                        {playersTotal !== null && (
                            <span className={panelStyles.panelCounter}>{playersTotal}</span>
                        )}
                    </div>
                    <AddPlayerButton teamId={teamId} onAdded={reloadPlayers} />
                </div>

                {playersLoading && (
                    <div className={styles.inlineState}>
                        <div className={styles.spinner} />
                        <span>Spelers laden…</span>
                    </div>
                )}

                {!playersLoading && playersError && (
                    <div className={styles.inlineState}>
                        <p className={styles.error}>{playersError}</p>
                        <button className={styles.retryBtn} onClick={reloadPlayers}>Opnieuw proberen</button>
                    </div>
                )}

                {!playersLoading && !playersError && players.length === 0 && (
                    <p className={commonStyles.muted}>Nog geen spelers in dit team. Voeg er hierboven toe.</p>
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
