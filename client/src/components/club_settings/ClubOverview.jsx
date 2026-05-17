// Club settings UI component for ClubOverview.

import styles from "@/style/ClubSettings.module.css";

export function ClubOverview({ club, texts = {} }) {
    /*
     Renders the static club overview cards.
    */
    return (
        <div className={`${styles.contentGrid} ${styles.contentFade}`}>

            {/* Club Info */}
            <article className={styles.panel}>
                <h3 className={styles.panelTitle}>{texts.overview_title || "Clubinformatie"}</h3>

                <ul className={styles.list}>
                    <li className={styles.listItem}>
                        <div>
                            <p className={styles.primaryText}>{club?.name}</p>
                            <p className={styles.secondaryText}>{texts.overview_name_label || "Naam"}</p>
                        </div>
                    </li>

                    <li className={styles.listItem}>
                        <div>
                            <p className={styles.primaryText}>{club?.city}</p>
                            <p className={styles.secondaryText}>{texts.overview_city_label || "Stad"}</p>
                        </div>
                    </li>

                    <li className={styles.listItem}>
                        <div>
                            <p className={styles.primaryText}>{club?.sport}</p>
                            <p className={styles.secondaryText}>{texts.overview_sport_label || "Sport"}</p>
                        </div>
                    </li>
                </ul>
            </article>

            {/* Description */}
            <article className={styles.panel}>
                <h3 className={styles.panelTitle}>{texts.overview_description_title || "Omschrijving"}</h3>

                <p className={styles.secondaryText}>
                    {club?.description || texts.overview_no_description || "Geen omschrijving opgegeven."}
                </p>
            </article>

        </div>
    );
}

export default ClubOverview;
