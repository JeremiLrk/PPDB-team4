// Team management UI component for TeamSettingsLink.

import { useNavigate } from "react-router-dom";
import styles from "@/style/TeamSettingsLink.module.css";
import GearIcon from "@/components/icon/GearIcon.jsx";
import { useLangContext } from "@/context/useLangContext.jsx";
import { usePageTexts } from "@/hooks/common/usePageTexts.js";

/**
 * Returns true if the user can open the team settings page.
 * - Administrator → always
 * - ClubOwner of the club owner of this team → yes
 * - TeamManager of this team → yes
 *
 * The logic mirrors _can_edit_team() on the server and canManageTeam() in TeamSettings.
 */
// eslint-disable-next-line react-refresh/only-export-components
export function canManageTeam(account, team) {
    /*
     Checks whether the current account may open team settings.
    */
    if (!account || !team) return false;
    const roles = Array.isArray(account.roles)
        ? account.roles
        : (account.role ? [account.role] : []);
    const role = roles[0] ?? account.role ?? null;
    if (!role) return false;

    if (role === "administrator") return true;

    if (role === "club_owner") {
        const ownsClub    = team.clubId && account.clubIds?.includes(team.clubId);
        const managesTeam = account.managedTeamIds?.includes(team.id);
        return ownsClub || managesTeam;
    }

    if (role === "team_manager") {
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
    const { lang } = useLangContext();
    const texts = usePageTexts("team_settings", lang);

    if (!canManageTeam(currentUser, team)) return null;
    /*
     Renders the settings shortcut only when the user has permission.
    */

    return (
        <button
            className={styles.gearBtn}
            title={texts.settings_title || "Team settings"}
            aria-label={`${texts.settings_aria || "Settings for"} ${team.name}`}
            onClick={e => {
                e.stopPropagation();
                navigate(`/teams/${team.id}/settings`);
            }}
        >
            <GearIcon size={size} title={texts.settings_title || "Team settings"} />
        </button>
    );
}
