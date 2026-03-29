import styles from "@/style/Dashboard.module.css";

export function ClubOverview({ club }) {
    return (
        <div className={`${styles.contentGrid} ${styles.contentFade}`}>

            {/* Club Info */}
            <article className={styles.panel}>
                <h3 className={styles.panelTitle}>Club Info</h3>

                <ul className={styles.list}>
                    <li className={styles.listItem}>
                        <div>
                            <p className={styles.primaryText}>{club?.name}</p>
                            <p className={styles.secondaryText}>Name</p>
                        </div>
                    </li>

                    <li className={styles.listItem}>
                        <div>
                            <p className={styles.primaryText}>{club?.city}</p>
                            <p className={styles.secondaryText}>City</p>
                        </div>
                    </li>

                    <li className={styles.listItem}>
                        <div>
                            <p className={styles.primaryText}>{club?.sport}</p>
                            <p className={styles.secondaryText}>Sport</p>
                        </div>
                    </li>
                </ul>
            </article>

            {/* Description */}
            <article className={styles.panel}>
                <h3 className={styles.panelTitle}>Description</h3>

                <p className={styles.secondaryText}>
                    {club?.description || "No description provided."}
                </p>
            </article>

        </div>
    );
}

export default ClubOverview;