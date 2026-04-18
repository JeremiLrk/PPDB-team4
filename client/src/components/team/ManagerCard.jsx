import commonStyles      from "@/style/common/Common.module.css";
import ItemCard           from "@/components/common/ItemCard.jsx";
import DeleteManagerButton from "@/components/team/DeleteManagerButton.jsx";

/**
 * ManagerCard — один рядок менеджера у списку команди.
 *
 * Props:
 *   manager    — { id, firstName, lastName, email, permissions: { canEditManagers, … } }
 *   teamId     — якщо передано, показує кнопку видалення
 *   canDelete  — чи може поточний користувач видаляти менеджерів
 *   onDeleted  — колбек після видалення
 */
export default function ManagerCard({ manager, teamId, canDelete, onDeleted }) {
    const fullName = [manager.firstName, manager.lastName]
        .filter(Boolean).join(" ") || "-";

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
                <PermissionsBadge permissions={manager.permissions} />

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

/* ── Мінімалістичний бейдж з іконками прав ──────────────────────────────── */

const PERM_ICONS = [
    { key: "canRename",       icon: "✏️", title: "Can rename"        },
    { key: "canDelete",       icon: "🗑️", title: "Can delete"        },
    { key: "canEditPlayers",  icon: "👥", title: "Can edit players"  },
    { key: "canEditManagers", icon: "🔑", title: "Can edit managers" },
];

function PermissionsBadge({ permissions }) {
    if (!permissions) return null;

    return (
        <span style={{
            display:      "flex",
            gap:          "0.15rem",
            alignItems:   "center",
        }}>
            {PERM_ICONS.map(({ key, icon, title }) => (
                <span
                    key={key}
                    title={title}
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
