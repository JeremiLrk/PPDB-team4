// Club settings UI component for ClubMembers.

import styles from "@/style/ClubSettings.module.css";

export function ClubMembers({ members, onRemove, texts = {} }) {
    /*
     Renders the club member list and remove actions.
    */
    return (
        <article className={`${styles.panel} ${styles.contentFade}`}>
            <div className={styles.panelTopRow}>
                <h3 className={styles.panelTitle}>{texts.members_title || "Leden"}</h3>
                <span className={styles.counter}>{members.length}</span>
            </div>

            {members.length === 0 ? (
                <p className={styles.muted}>{texts.no_members || "Nog geen leden."}</p>
            ) : (
                <ul className={styles.list}>
                    {members.map(m => (
                        <li key={m.id} className={styles.listItem}>
                            <div>
                                <p className={styles.primaryText}>{m.email}</p>
                            </div>

                            <button
                                onClick={() => onRemove(m.id)}
                                className={styles.linkButton}
                            >
                                {texts.remove || "Verwijderen"}
                            </button>
                        </li>
                    ))}
                </ul>
            )}
        </article>
    );
}

export default ClubMembers;
