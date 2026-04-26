import { useNavigate, useParams } from "react-router-dom";
import styles from "@/style/Home.module.css";

function ClubSidebar({ activeTab, onTabChange }) {
    const { clubId } = useParams();
    const navigate = useNavigate();

    return (
        <aside className={styles.ladderAside}>
            <section className={styles.ladderContainer}>
                <h2 className={styles.ladderContainerText}>Settings</h2>

                <div className={styles.ladderCard}>
                    <button
                        className={`${styles.ladderButton} ${
                            activeTab === "general" ? "bg-indigo-500/20 border-l-4 border-indigo-500" : ""
                        }`}
                        onClick={() => onTabChange("general")}
                    >
                        General Info
                    </button>

                    <button
                        className={`${styles.ladderButton} ${
                            activeTab === "ladders" ? "bg-indigo-500/20 border-l-4 border-indigo-500" : ""
                        }`}
                        onClick={() => onTabChange("ladders")}
                    >
                        Ladders
                    </button>

                    <button
                        className={`${styles.ladderButton} ${
                            activeTab === "members" ? "bg-indigo-500/20 border-l-4 border-indigo-500" : ""
                        }`}
                        onClick={() => onTabChange("members")}
                    >
                        Members
                    </button>

                    <button
                        className={`${styles.ladderButton} ${
                            activeTab === "rules" ? "bg-indigo-500/20 border-l-4 border-indigo-500" : ""
                        }`}
                        onClick={() => onTabChange("rules")}
                    >
                        Match Rules
                    </button>

                    <button
                        className={`${styles.ladderButton} ${
                            activeTab === "owners" ? "bg-indigo-500/20 border-l-4 border-indigo-500" : ""
                        }`}
                        onClick={() => onTabChange("owners")}
                    >
                        owners
                    </button>

                    <button
                        className={styles.ladderButton}
                        onClick={() => navigate(`/clubs/${clubId}`)}
                    >
                        Go to Club Home
                    </button>
                </div>
            </section>
        </aside>
    );
}

export default ClubSidebar;
