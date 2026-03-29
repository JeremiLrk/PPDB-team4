import commonStyles from "@/style/common/Common.module.css";
import ItemCard from "@/components/common/ItemCard.jsx";

/**
 * PlayerCard — a single player line in a team list.
 *
 * Props:
 *   player — { id, playerId, email, firstName?, lastName? }
 */
export default function PlayerCard({ player }) {
    const fullName = [player.firstName, player.lastName].filter(Boolean).join(" ") || "—";

    return (
        <ItemCard>
            <div>
                <p className={commonStyles.primaryText}>{fullName}</p>
                <p className={commonStyles.secondaryText}>{player.email}</p>
            </div>
            <span className={commonStyles.muted} style={{ fontSize: "0.78rem", whiteSpace: "nowrap" }}>
                #{player.playerId ?? player.id}
            </span>
        </ItemCard>
    );
}
