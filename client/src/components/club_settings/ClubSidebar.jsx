import { useNavigate, useParams } from "react-router-dom";
import styles from "@/style/Home.module.css";

function ClubSidebar({ activeTab, onTabChange, texts = {} }) {
    const { clubId } = useParams();
    const navigate = useNavigate();

    return (
        <aside className={styles.ladderAside}>
            <section className={styles.ladderContainer}>
                <h2 className={styles.ladderContainerText}>{texts.sidebar_title || "Instellingen"}</h2>

                <div className={styles.ladderCard}>
                    <button
                        className={`${styles.ladderButton} ${
                            activeTab === "general" ? "bg-indigo-500/20 border-l-4 border-indigo-500" : ""
                        }`}
                        onClick={() => onTabChange("general")}
                    >
                        {texts.tab_general || "Algemene info"}
                    </button>

                    <button
                        className={`${styles.ladderButton} ${
                            activeTab === "ladders" ? "bg-indigo-500/20 border-l-4 border-indigo-500" : ""
                        }`}
                        onClick={() => onTabChange("ladders")}
                    >
                        {texts.tab_ladders || "Ladders"}
                    </button>

                    <button
                        className={`${styles.ladderButton} ${
                            activeTab === "members" ? "bg-indigo-500/20 border-l-4 border-indigo-500" : ""
                        }`}
                        onClick={() => onTabChange("members")}
                    >
                        {texts.tab_members || "Leden"}
                    </button>

                    <button
                        className={`${styles.ladderButton} ${
                            activeTab === "rules" ? "bg-indigo-500/20 border-l-4 border-indigo-500" : ""
                        }`}
                        onClick={() => onTabChange("rules")}
                    >
                        {texts.tab_rules || "Wedstrijdregels"}
                    </button>

                    <button
                        className={`${styles.ladderButton} ${
                            activeTab === "owners" ? "bg-indigo-500/20 border-l-4 border-indigo-500" : ""
                        }`}
                        onClick={() => onTabChange("owners")}
                    >
                        {texts.tab_owners || "Eigenaren"}
                    </button>

                    <button
                        className={`${styles.ladderButton} ${
                            activeTab === "disputed" ? "bg-red-500/20 border-l-4 border-red-500" : ""
                        }`}
                        onClick={() => navigate(`/clubs/${clubId}/settings/disputed`)}
                    >
                        {texts.tab_disputed || "Disputed matches"}
                    </button>

                    <button
                        className={styles.ladderButton}
                        onClick={() => navigate(`/clubs/${clubId}`)}
                    >
                        {texts.tab_home || "Naar clubhome"}
                    </button>
                </div>
            </section>
        </aside>
    );
}

export default ClubSidebar;
