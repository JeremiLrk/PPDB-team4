import { useNavigate } from "react-router-dom";
import styles from "@/style/TeamSettingsLink.module.css";
import GearIcon from "@/components/icon/GearIcon.jsx";

/**
 * Returns true if the user can open the team settings page.
 * - Administrator → always
 * - ClubOwner of the club owner of this team → yes
 * - TeamManager of this team → yes
 *
 * The logic mirrors _can_edit_team() on the server and canManageTeam() in TeamSettings.
 */
export function canManageTeam(account, team) {
    if (!account || !team) return false;
    const roles = account.roles ?? [];

    if (roles.includes("administrator")) return true;

    if (roles.includes("club_owner")) {
        const ownsClub    = team.clubId && account.clubIds?.includes(team.clubId);
        const managesTeam = account.managedTeamIds?.includes(team.id);
        return ownsClub || managesTeam;
    }

    if (roles.includes("team_manager")) {
        return account.managedTeamIds?.includes(team.id);
    }

    return false;
}


/**
 * TeamSettingsLink — a ⚙ button icon that links to /teams/:teamId/settings.
 * Rendered only if the current user can manage the team.
 *
 * Props:
 * currentUser — an object from the useCurrentUserContext context
 * team — a team object { id, clubId, ... }
 * size — the size of the icon (default: 18)
 */
export default function TeamSettingsLink({ currentUser, team, size = 18 }) {
    const navigate = useNavigate();

    if (!canManageTeam(currentUser, team)) return null;

    return (
        <button
            className={styles.gearBtn}
            title="Team settings"
            aria-label={`Settings for ${team.name}`}
            onClick={e => {
                e.stopPropagation();
                navigate(`/teams/${team.id}/settings`);
            }}
        >
            <GearIcon size={size} title="Team settings" />
        </button>
    );
}
