import { useNavigate } from "react-router-dom";
import styles from "@/style/Landing.module.css";
import { useLangContext } from "@/context/useLangContext.jsx";
import { usePageTexts } from "@/hooks/common/usePageTexts.js";

function Landing() {
    const navigate = useNavigate();
    const { lang } = useLangContext();
    const landingTexts = usePageTexts("landing", lang);

    if (!landingTexts.explore_clubs) {
        return <div className={styles.page} />;
    }

    const playerSteps = [
        {
            title: landingTexts.player_step_1_title || "Create account",
            description: landingTexts.player_step_1_description || "Sign up to get access to your dashboard.",
        },
        {
            title: landingTexts.player_step_2_title || "Find clubs and request to join",
            description:
                landingTexts.player_step_2_description ||
                "Search clubs and send a join request to the one you want.",
        },
        {
            title: landingTexts.player_step_3_title || "Get accepted and placed in ladders",
            description:
                landingTexts.player_step_3_description ||
                "A club manager accepts your request and adds you to the right ladders.",
        },
    ];

    const managerSteps = [
        {
            title: landingTexts.manager_step_1_title || "Create account",
            description: landingTexts.manager_step_1_description || "Sign up to get access to your dashboard.",
        },
        {
            title: landingTexts.manager_step_2_title || "Request your own club",
            description: landingTexts.manager_step_2_description || "Submit your club creation request.",
        },
        {
            title: landingTexts.manager_step_3_title || "Manage club ladders",
            description:
                landingTexts.manager_step_3_description ||
                "Create, update, and manage ladders and members in your club.",
        },
    ];

    return (
        <div className={styles.page}>
            <section className={styles.hero}>
                <p className={styles.kicker}>{landingTexts.kicker || "Club ladder platform"}</p>
                <h1 className={styles.title}>
                    <span className={styles.titleGradient}>NetRank</span>
                </h1>
                <div className={styles.actions}>
                    <button onClick={() => navigate("/clubs")} className={styles.primaryButton}>
                        {landingTexts.explore_clubs || "Explore clubs"}
                    </button>
                    <button onClick={() => navigate("/dashboard")} className={styles.secondaryButton}>
                        {landingTexts.open_dashboard || "Open dashboard"}
                    </button>
                </div>
            </section>

            <section className={styles.stepsSection}>
                <h2>{landingTexts.how_it_works || "How NetRank works"}</h2>
                <div className={styles.dualTimelines}>
                    <article className={styles.timelineColumn}>
                        <h3 className={styles.columnTitle}>{landingTexts.as_player || "As a Player"}</h3>
                        <ol className={styles.altTimeline}>
                            {playerSteps.map((step, index) => (
                                <li key={step.title} className={styles.altItem}>
                                    <span className={styles.altDot} aria-hidden="true" />
                                    <div
                                        className={`${styles.altCard} ${
                                            index % 2 === 0 ? styles.sideLeft : styles.sideRight
                                        }`}
                                    >
                                        <span className={styles.altMeta}>
                                            {(landingTexts.step_label || "Step") + " " + (index + 1)}
                                        </span>
                                        <h4>{step.title}</h4>
                                        <p>{step.description}</p>
                                    </div>
                                </li>
                            ))}
                        </ol>
                    </article>

                    <article className={styles.timelineColumn}>
                        <h3 className={styles.columnTitle}>{landingTexts.as_manager || "As a Club Manager"}</h3>
                        <ol className={styles.altTimeline}>
                            {managerSteps.map((step, index) => (
                                <li key={step.title} className={styles.altItem}>
                                    <span className={styles.altDot} aria-hidden="true" />
                                    <div
                                        className={`${styles.altCard} ${
                                            index % 2 === 0 ? styles.sideLeft : styles.sideRight
                                        }`}
                                    >
                                        <span className={styles.altMeta}>
                                            {(landingTexts.step_label || "Step") + " " + (index + 1)}
                                        </span>
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
