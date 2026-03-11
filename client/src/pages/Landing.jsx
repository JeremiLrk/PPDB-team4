import { useNavigate } from "react-router-dom";
import styles from "@/style/Landing.module.css";

function Landing() {
    const navigate = useNavigate();

    return (
        <div className={styles.page}>
            <div className={styles.background}>
                <div className={styles.glowTop} />
                <div className={styles.glowBottom} />
            </div>

            <section className={styles.hero}>
                <h1 className={styles.title}>
                    <span className={styles.titleAccent}>NetRank</span>
                </h1>

                <p className={styles.kicker}>Web-based club ladder platform</p>

                <div className={styles.actions}>
                    <button onClick={() => navigate("/clubs")} className={styles.primaryButton}>
                        Browse Clubs
                    </button>
                    <button onClick={() => navigate("/dashboard")} className={styles.secondaryButton}>
                        Dashboard
                    </button>
                </div>
            </section>
        </div>
    );
}

export default Landing;
