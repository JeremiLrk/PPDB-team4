// Team management UI component for ManagerCard.

import commonStyles      from "@/style/common/Common.module.css";
import ItemCard           from "@/components/common/ItemCard.jsx";
import DeleteManagerButton from "@/components/team/DeleteManagerButton.jsx";
import { useLangContext } from "@/context/useLangContext.jsx";
import { usePageTexts } from "@/hooks/common/usePageTexts.js";

/**
 * ManagerCard — one line of the manager in the team list.
 *
 * Props:
 * manager — { id, firstName, lastName, email, permissions: { canEditManagers, … } }
 * teamId — if passed, shows the delete button
 * canDelete — whether the current user can delete managers
 * onDeleted — callback after deletion
 */
export default function ManagerCard({ manager, teamId, canDelete, onDeleted }) {
    const { lang } = useLangContext();
    const texts = usePageTexts("team_settings", lang);
    const fullName = [manager.firstName, manager.lastName]
        .filter(Boolean).join(" ") || "-";
    /*
     Renders one manager row with permission badges and delete action.
    */

    return (
        <ItemCard>
            <div>
                <p className={commonStyles.primaryText}>{fullName}</p>
                <p className={commonStyles.secondaryText}>{manager.email}</p>
            </div>

            <div style={{
                display:    "flex",
                alignItems: "center",
                gap:        "0.6rem",
                flexShrink: 0,
            }}>
                {/* Бейдж прав — компактний список */}
                <PermissionsBadge permissions={manager.permissions} texts={texts} />

                <span className={commonStyles.muted}
                      style={{ fontSize: "0.78rem", whiteSpace: "nowrap" }}>
                    #{manager.id}
                </span>

                {teamId && canDelete && (
                    <DeleteManagerButton
                        teamId={teamId}
                        managerId={manager.id}
                        onDeleted={onDeleted}
                    />
                )}
            </div>
        </ItemCard>
    );
}

/* -- Minimalist badge with rights icons -------------------------------- */

const PERM_ICONS = [
    { key: "canRename",       icon: "✏️", textKey: "perm_can_rename" },
    { key: "canDelete",       icon: "🗑️", textKey: "perm_can_delete" },
    { key: "canEditPlayers",  icon: "👥", textKey: "perm_can_edit_players" },
    { key: "canEditManagers", icon: "🔑", textKey: "perm_can_edit_managers" },
];

function PermissionsBadge({ permissions, texts = {} }) {
    /*
     Renders the manager permission badge row.
    */
    if (!permissions) return null;

    return (
        <span style={{
            display:      "flex",
            gap:          "0.15rem",
            alignItems:   "center",
        }}>
            {PERM_ICONS.map(({ key, icon, textKey }) => (
                <span
                    key={key}
                    title={texts[textKey] || ""}
                    style={{
                        fontSize:  "0.78rem",
                        opacity:   permissions[key] ? 1 : 0.2,
                        filter:    permissions[key] ? "none" : "grayscale(1)",
                        cursor:    "default",
                    }}
                >
                    {icon}
                </span>
            ))}
        </span>
    );
}
