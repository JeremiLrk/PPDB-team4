import { useNavigate } from "react-router-dom";
import commonStyles from "@/style/common/Common.module.css";
import buttonStyles from "@/style/common/Buttons.module.css";
import dashboardStyles from "@/style/dashboard/Dashboard.module.css";
import { useThemeContext } from "@/context/useThemeContext.jsx";

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
export default function TeamCard({ team, texts, currentUser, onClick, theme }) {
    const navigate = useNavigate();
    const { theme: contextTheme } = useThemeContext();
    const isLight = (theme || contextTheme) === "light";

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
                <p
                    className={dashboardStyles.teamCardName}
                    style={{
                        color: isLight ? "#020617" : "#ffffff",
                        WebkitTextFillColor: isLight ? "#020617" : "#ffffff",
                    }}
                >
                    {team.name}
                </p>
                <p
                    className={dashboardStyles.teamCardMeta}
                    style={{
                        color: isLight ? "#334155" : "#cbd5e1",
                        WebkitTextFillColor: isLight ? "#334155" : "#cbd5e1",
                    }}
                >
                    {team.clubName
                        ? team.clubName
                        : texts?.independent_team || "Independent"}
                    {team.sportName ? ` · ${team.sportName}` : ""}
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
