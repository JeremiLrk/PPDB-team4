import { useNavigate, useParams } from "react-router-dom";
import styles from "@/style/ClubSettings.module.css";

function ClubSidebar({ activeTab, onTabChange, texts = {} }) {
    const { clubId } = useParams();
    const navigate = useNavigate();

    return (
        <aside className={styles.sidebar}>
            <h2 className={styles.sidebarTitle}>{texts.sidebar_title || "Instellingen"}</h2>

            {/* These remain plain buttons so the shell can switch tabs without form-submit side effects. */}
            <nav className={styles.nav} aria-label={texts.sidebar_title || "Instellingen"}>
                <button
                    type="button"
                    className={`${styles.navButton} ${activeTab === "general" ? styles.navButtonActive : ""}`}
                    onClick={() => onTabChange("general")}
                >
                    {texts.tab_general || "Algemene info"}
                </button>

                <button
                    type="button"
                    className={`${styles.navButton} ${activeTab === "ladders" ? styles.navButtonActive : ""}`}
                    onClick={() => onTabChange("ladders")}
                >
                    {texts.tab_ladders || "Ladders"}
                </button>

                <button
                    type="button"
                    className={`${styles.navButton} ${activeTab === "members" ? styles.navButtonActive : ""}`}
                    onClick={() => onTabChange("members")}
                >
                    {texts.tab_members || "Leden"}
                </button>

                <button
                    type="button"
                    className={`${styles.navButton} ${activeTab === "rules" ? styles.navButtonActive : ""}`}
                    onClick={() => onTabChange("rules")}
                >
                    {texts.tab_rules || "Wedstrijdregels"}
                </button>

                <button
                    type="button"
                    className={`${styles.navButton} ${activeTab === "owners" ? styles.navButtonActive : ""}`}
                    onClick={() => onTabChange("owners")}
                >
                    {texts.tab_owners || "Eigenaren"}
                </button>

                <button
                    type="button"
                    className={`${styles.navButton} ${activeTab === "disputed" ? styles.navButtonActive : ""}`}
                    onClick={() => navigate(`/clubs/${clubId}/settings/disputed`)}
                >
                    {texts.tab_disputed || "Disputed matches"}
                </button>

                {/* Return to the public club page from anywhere in settings. */}
                <button
                    type="button"
                    className={styles.navButton}
                    onClick={() => navigate(`/clubs/${clubId}`)}
                >
                    {texts.tab_home || "Naar clubhome"}
                </button>
            </nav>
        </aside>
    );
}

export default ClubSidebar;
