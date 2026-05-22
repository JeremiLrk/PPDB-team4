// Page container for Landing.

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
            title: landingTexts.player_step_1_title,
            description: landingTexts.player_step_1_description,
        },
        {
            title: landingTexts.player_step_2_title,
            description: landingTexts.player_step_2_description,
        },
        {
            title: landingTexts.player_step_3_title,
            description: landingTexts.player_step_3_description,
        },
    ];

    const managerSteps = [
        {
            title: landingTexts.manager_step_1_title,
            description: landingTexts.manager_step_1_description,
        },
        {
            title: landingTexts.manager_step_2_title,
            description: landingTexts.manager_step_2_description,
        },
        {
            title: landingTexts.manager_step_3_title,
            description: landingTexts.manager_step_3_description,
        },
    ];

    return (
        <div className={styles.page}>
            <section className={styles.hero}>
                <p className={styles.kicker}>{landingTexts.kicker}</p>
                <h1 className={styles.title}>
                    <span className={styles.titleGradient}>NetRank</span>
                </h1>
                <div className={styles.actions}>
                    <button onClick={() => navigate("/clubs")} className={styles.primaryButton}>
                        {landingTexts.explore_clubs}
                    </button>
                    <button onClick={() => navigate("/dashboard")} className={styles.secondaryButton}>
                        {landingTexts.open_dashboard}
                    </button>
                </div>
            </section>

            <section className={styles.stepsSection}>
                <h2>{landingTexts.how_it_works}</h2>
                <div className={styles.dualTimelines}>
                    <article className={styles.timelineColumn}>
                        <h3 className={styles.columnTitle}>{landingTexts.as_player}</h3>
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
                                            {landingTexts.step_label + " " + (index + 1)}
                                        </span>
                                        <h4>{step.title}</h4>
                                        <p>{step.description}</p>
                                    </div>
                                </li>
                            ))}
                        </ol>
                    </article>

                    <article className={styles.timelineColumn}>
                        <h3 className={styles.columnTitle}>{landingTexts.as_manager}</h3>
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
                                            {landingTexts.step_label + " " + (index + 1)}
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
