import { useNavigate } from "react-router-dom";
import panelStyles from "@/style/common/Panel.module.css";
import discoverStyles from "@/style/common/DiscoverGrid.module.css";
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
                <p className={panelStyles.primaryText}>{team.name}</p>
                <p className={panelStyles.secondaryText}>
                    {team.clubId
                        ? `Club #${team.clubId}`
                        : texts?.independent_team || "Independent"}
                    {team.sportTypeId ? ` · Sport #${team.sportTypeId}` : ""}
                </p>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
                <TeamSettingsLink currentUser={currentUser} team={team} />
                <button className={discoverStyles.linkButton} onClick={handleOpen}>
                    {texts?.open || "Open"}
                </button>
            </div>
        </ItemCard>
    );
}
