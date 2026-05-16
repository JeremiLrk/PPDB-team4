import { useNavigate, useParams } from "react-router-dom";
import styles from "@/style/ClubSettings.module.css";

function ClubSidebar({ activeTab, onTabChange, texts = {} }) {
    const { clubId } = useParams();
    const navigate = useNavigate();

    function navClass(tab) {
        return `${styles.navButton} ${activeTab === tab ? styles.navButtonActive : ""}`;
    }

    return (
        <aside className={styles.sidebar}>
            <p className={styles.brand}>{texts.sidebar_title || "Instellingen"}</p>

            <nav className={styles.nav} aria-label={texts.sidebar_title || "Instellingen"}>
                <button type="button" className={navClass("general")} onClick={() => onTabChange("general")}>
                    {texts.tab_general || "Algemene info"}
                </button>
                <button type="button" className={navClass("ladders")} onClick={() => onTabChange("ladders")}>
                    {texts.tab_ladders || "Ladders"}
                </button>
                <button type="button" className={navClass("members")} onClick={() => onTabChange("members")}>
                    {texts.tab_members || "Leden"}
                </button>
                <button type="button" className={navClass("rules")} onClick={() => onTabChange("rules")}>
                    {texts.tab_rules || "Wedstrijdregels"}
                </button>
                <button type="button" className={navClass("owners")} onClick={() => onTabChange("owners")}>
                    {texts.tab_owners || "Eigenaren"}
                </button>
                <button
                    type="button"
                    className={`${styles.navButton} ${activeTab === "disputed" ? styles.navButtonActiveDanger : ""}`}
                    onClick={() => navigate(`/clubs/${clubId}/settings/disputed`)}
                >
                    {texts.tab_disputed || "Disputed matches"}
                </button>
            </nav>

            <div className={styles.sidebarFooter}>
                <button type="button" className={styles.navButton} style={{ width: "100%" }} onClick={() => navigate(`/clubs/${clubId}`)}>
                    {texts.tab_home || "Naar clubhome"}
                </button>
            </div>
        </aside>
    );
}

export default ClubSidebar;
