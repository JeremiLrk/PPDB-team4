import { useNavigate } from "react-router-dom";
import styles from "@/style/Landing.module.css";

const playerSteps = [
    {
        title: "Create account",
        description: "Sign up to get access to your dashboard.",
    },
    {
        title: "Find clubs and request to join",
        description: "Search clubs and send a join request to the one you want.",
    },
    {
        title: "Get accepted and placed in ladders",
        description: "A club manager accepts your request and adds you to the right ladders.",
    },
];

const managerSteps = [
    {
        title: "Create account",
        description: "Sign up to get access to your dashboard.",
    },
    {
        title: "Request your own club",
        description: "Submit your club creation request.",
    },
    {
        title: "Manage club ladders",
        description: "Create, update, and manage ladders and members in your club.",
    },
];

function Landing() {
    const navigate = useNavigate();

    return (
        <div className={styles.page}>
            <section className={styles.hero}>
                <p className={styles.kicker}>Club ladder platform</p>
                <h1 className={styles.title}>
                    <span className={styles.titleGradient}>NetRank</span>
                </h1>
                <div className={styles.actions}>
                    <button onClick={() => navigate("/clubs")} className={styles.primaryButton}>
                        Explore clubs
                    </button>
                    <button onClick={() => navigate("/dashboard")} className={styles.secondaryButton}>
                        Open dashboard
                    </button>
                </div>
            </section>

            <section className={styles.stepsSection}>
                <h2>How NetRank works</h2>
                <div className={styles.dualTimelines}>
                    <article className={styles.timelineColumn}>
                        <h3 className={styles.columnTitle}>As a Player</h3>
                        <ol className={styles.altTimeline}>
                            {playerSteps.map((step, index) => (
                                <li key={step.title} className={styles.altItem}>
                                    <span className={styles.altDot} aria-hidden="true" />
                                    <div
                                        className={`${styles.altCard} ${
                                            index % 2 === 0 ? styles.sideLeft : styles.sideRight
                                        }`}
                                    >
                                        <span className={styles.altMeta}>Step {index + 1}</span>
                                        <h4>{step.title}</h4>
                                        <p>{step.description}</p>
                                    </div>
                                </li>
                            ))}
                        </ol>
                    </article>

                    <article className={styles.timelineColumn}>
                        <h3 className={styles.columnTitle}>As a Club Manager</h3>
                        <ol className={styles.altTimeline}>
                            {managerSteps.map((step, index) => (
                                <li key={step.title} className={styles.altItem}>
                                    <span className={styles.altDot} aria-hidden="true" />
                                    <div
                                        className={`${styles.altCard} ${
                                            index % 2 === 0 ? styles.sideLeft : styles.sideRight
                                        }`}
                                    >
                                        <span className={styles.altMeta}>Step {index + 1}</span>
                                        <h4>{step.title}</h4>
                                        <p>{step.description}</p>
                                    </div>
                                </li>
                            ))}
                        </ol>
                    </article>
                </div>
            </section>
        </div>
    );
}

export default Landing;
