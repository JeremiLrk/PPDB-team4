import styles from "@/style/ClubSettings.module.css";

export function ClubGeneral({
    formData,
    onChange,
    onSubmit,
    updating,
    updateMessage,
}) {
    return (
        <article className={`${styles.panel} ${styles.contentFade}`}>
            <h3 className={styles.panelTitle}>General Settings</h3>

            <form className={styles.form} onSubmit={onSubmit}>
                <label className={styles.formLabel}>
                    Club Name
                    <input
                        className={styles.formInput}
                        type="text"
                        name="name"
                        value={formData.name}
                        onChange={onChange}
                        required
                    />
                </label>

                <div className={styles.formRow}>
                    <label className={styles.formLabel}>
                        City
                        <input
                            className={styles.formInput}
                            type="text"
                            name="city"
                            value={formData.city}
                            onChange={onChange}
                        />
                    </label>

                    <label className={styles.formLabel}>
                        Sport
                        <input
                            className={styles.formInput}
                            type="text"
                            name="sport"
                            value={formData.sport}
                            onChange={onChange}
                        />
                    </label>
                </div>

                <label className={styles.formLabel}>
                    Description
                    <textarea
                        className={styles.formTextarea}
                        name="description"
                        value={formData.description}
                        onChange={onChange}
                        rows={4}
                    />
                </label>

                <div className={styles.formActions}>
                    <button
                        type="submit"
                        className={styles.submitButton}
                        disabled={updating}
                    >
                        {updating ? "Saving..." : "Save Changes"}
                    </button>
                </div>
            </form>

            {updateMessage && (
                <p
                    className={
                        updateMessage.type === "error"
                            ? styles.warning
                            : styles.notice
                    }
                >
                    {updateMessage.text}
                </p>
            )}
        </article>
    );
}

export default ClubGeneral;