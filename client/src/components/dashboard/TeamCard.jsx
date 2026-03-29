import { useNavigate } from "react-router-dom";
import styles from "@/style/common/Common.module.css";
import ItemCard from "@/components/common/ItemCard.jsx";

/**
 * TeamCard — a box for one team in the list.
 *
 * Props:
 * team — { id, name, clubId?, sportTypeId? }
 * texts — localization object (optional)
 * onClick — custom handler for the "Open" button click;
 *             if not passed — navigate to /teams/:id
 */
export default function TeamCard({ team, texts, onClick }) {
    const navigate = useNavigate();

    function handleOpen() {
        if (onClick) {
            onClick(team);
        } else {
            navigate(`/teams/${team.id}`);
        }
    }

    return (
        <ItemCard>
            <div>
                <p className={styles.primaryText}>{team.name}</p>
                <p className={styles.secondaryText}>
                    {team.clubId
                        ? `Club #${team.clubId}`
                        : texts?.independent_team || "Independent"}
                    {team.sportTypeId ? ` · Sport #${team.sportTypeId}` : ""}
                </p>
            </div>
            <button className={styles.linkButton} onClick={handleOpen}>
                {texts?.open || "Open"}
            </button>
        </ItemCard>
    );
}
