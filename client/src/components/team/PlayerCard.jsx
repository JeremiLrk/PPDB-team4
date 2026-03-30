import commonStyles from "@/style/common/Common.module.css";
import ItemCard from "@/components/common/ItemCard.jsx";
import DeletePlayerButton from "@/components/team/DeletePlayerButton.jsx";

/**
 * PlayerCard - a single player line in a team list.
 *
 * Props:
 *   player    - { id, playerId, accountId?, email, firstName?, lastName? }
 *   teamId    - if provided, shows a delete button
 *   onDeleted - called after the player is removed
 */
export default function PlayerCard({ player, teamId, onDeleted }) {
    const fullName  = [player.firstName, player.lastName].filter(Boolean).join(" ") || "-";
    const accountId = player.accountId ?? player.id;

    return (
        <ItemCard>
            <div>
                <p className={commonStyles.primaryText}>{fullName}</p>
                <p className={commonStyles.secondaryText}>{player.email}</p>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "0.6rem", flexShrink: 0 }}>
                <span className={commonStyles.muted} style={{ fontSize: "0.78rem", whiteSpace: "nowrap" }}>
                    #{player.playerId ?? player.id}
                </span>
                {teamId && (
                    <DeletePlayerButton
                        teamId={teamId}
                        playerId={accountId}
                        onDeleted={onDeleted}
                    />
                )}
            </div>
        </ItemCard>
    );
}
