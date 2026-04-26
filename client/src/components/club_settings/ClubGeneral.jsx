import styles from "@/style/ClubSettings.module.css";

export function ClubGeneral({
    formData,
    onChange,
    onSubmit,
    updating,
    updateMessage,
    sportTypes = [], // Default to empty array to avoid map errors
    texts = {},
}) {
    return (
        <article className={`${styles.panel} ${styles.contentFade}`}>
            <h3 className={styles.panelTitle}>{texts.general_title || "Algemene instellingen"}</h3>

            <form className={styles.form} onSubmit={onSubmit}>
                {/* CLUB NAME */}
                <label className={styles.formLabel}>
                    {texts.club_name || "Clubnaam"}
                    <input
                        className={styles.formInput}
                        type="text"
                        name="name"
                        value={formData.name || ""}
                        onChange={onChange}
                        required
                    />
                </label>

                <div className={styles.formRow}>
                    {/* CITY */}
                    <label className={styles.formLabel}>
                        {texts.city || "Stad"}
                        <input
                            className={styles.formInput}
                            type="text"
                            name="city"
                            value={formData.city || ""}
                            onChange={onChange}
                        />
                    </label>

                    {/* SPORT SELECTION (Dropdown) */}
                    <label className={styles.formLabel}>
                            {texts.sport || "Sport"}
                        <select
                            className={styles.formInput}
                            name="sport_type_id"
                            value={formData.sport_type_id || ""}
                            onChange={onChange}
                            required
                        >
                            <option value="" disabled>
                                {texts.choose_sport || "Kies een sport"}
                            </option>
                            {sportTypes.map((sport) => (
                                <option key={sport.id} value={sport.id}>
                                    {sport.name}
                                </option>
                            ))}
                        </select>
                    </label>
                </div>

                {/* DESCRIPTION */}
                <label className={styles.formLabel}>
                    {texts.description || "Omschrijving"}
                    <textarea
                        className={styles.formTextarea}
                        name="description"
                        value={formData.description || ""}
                        onChange={onChange}
                        rows={4}
                    />
                </label>

                {/* SUBMIT ACTION */}
                <div className={styles.formActions}>
                    <button
                        type="submit"
                        className={styles.submitButton}
                        disabled={updating}
                    >
                        {updating ? (texts.saving || "Opslaan...") : (texts.save_changes || "Wijzigingen opslaan")}
                    </button>
                </div>
            </form>

            {/* STATUS MESSAGES */}
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
