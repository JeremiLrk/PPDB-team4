import { useNavigate } from "react-router-dom";
import GearIcon from "@/components/icon/GearIcon.jsx";
import styles   from "@/style/TeamSettingsLink.module.css";

/**
 * Повертає true, якщо користувач може відкрити сторінку налаштувань команди.
 *   - Administrator           → завжди
 *   - ClubOwner власника клубу цієї команди → так
 *   - TeamManager цієї команди              → так
 *
 * Логіка дзеркалює _can_edit_team() на сервері та canManageTeam() у TeamSettings.
 */
export function canManageTeam(user, team) {
    if (!user || !team) return false;
    const role = user.role;

    if (role === "administrator") return true;

    if (role === "club_owner") {
        const ownsClub    = team.clubId && user.clubIds?.includes(team.clubId);
        const managesTeam = user.managedTeamIds?.includes(team.id);
        return ownsClub || managesTeam;
    }

    if (role === "team_manager") {
        return user.managedTeamIds?.includes(team.id);
    }

    return false;
}

/**
 * TeamSettingsLink — іконка-кнопка ⚙, яка веде на /teams/:teamId/settings.
 * Рендериться лише якщо поточний користувач може керувати командою.
 *
 * Props:
 *   currentUser — об'єкт з контексту useCurrentUserContext
 *   team        — об'єкт команди { id, clubId, ... }
 *   size        — розмір іконки (default: 18)
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
