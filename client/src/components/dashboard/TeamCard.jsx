import { useNavigate } from "react-router-dom";
import commonStyles from "@/style/common/Common.module.css";
import buttonStyles from "@/style/common/Buttons.module.css";

import ItemCard from "@/components/common/ItemCard.jsx";
import TeamSettingsLink from "@/components/team/TeamSettingsLink.jsx";

/**
 * TeamCard — a box for one team in the list.
 *
 * Props:
 * team — { id, name, clubId?, sportTypeId? }
 * texts — localization object (optional)
 * currentUser — current user (to display the ⚙ button)
 * onClick — custom handler for the "Open" button click;
 * if not passed — navigate to /teams/:id
 */
export default function TeamCard({ team, texts, currentUser, onClick }) {
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
                <p className={commonStyles.primaryText}>{team.name}</p>
                <p className={commonStyles.secondaryText}>
                    {team.clubId
                        ? `Club #${team.clubId}`
                        : texts?.independent_team || "Onafhankelijk"}
                    {team.sportTypeId ? ` · Sport #${team.sportTypeId}` : ""}
                </p>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
                <TeamSettingsLink currentUser={currentUser} team={team} />
                <button className={buttonStyles.linkButton} onClick={handleOpen}>
                    {texts?.open || "Openen"}
                </button>
            </div>
        </ItemCard>
    );
}
