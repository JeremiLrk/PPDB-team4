import { useState } from "react";
import styles from "@/style/ClubSettings.module.css";

export function ClubGeneral({
    formData,
    onChange,
    onSubmit,
    updating,
    updateMessage,
    sportTypes = [],
    handleDeleteClub,
    texts = {},
}) {
    // State for the delete confirmation modal
    const [showDeleteModal, setShowDeleteModal] = useState(false);
    const [confirmName, setConfirmName] = useState("");

    const onConfirmDelete = () => {
        handleDeleteClub();
        setShowDeleteModal(false);
        setConfirmName(""); // Reset just in case
    };

    return (
        <div className={styles.contentFade}>
            {/* --- GENERAL SETTINGS FORM --- */}
            <article className={styles.panel}>
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

                        {/* SPORT SELECTION */}
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

            {/* --- DANGER ZONE --- */}
            <article className={`${styles.panel} ${styles.dangerZone}`}>
                <div className={styles.dangerHeader}>
                    <h3 className={styles.dangerTitle}>{texts.danger_zone || "Gevarenzone"}</h3>
                </div>
                <div className={styles.dangerContent}>
                    <div className={styles.dangerText}>
                        <strong>{texts.delete_club_warning || "Verwijder deze club"}</strong>
                        <p>{texts.delete_club_subtext || "Zodra je een club verwijdert, is er geen weg meer terug. Wees alsjeblieft zeker."}</p>
                    </div>
                    <button 
                        type="button" 
                        className={styles.deleteButton}
                        onClick={() => setShowDeleteModal(true)}
                    >
                        {texts.delete_club || "Club Verwijderen"}
                    </button>
                </div>
            </article>

            {/* --- DELETE CONFIRMATION MODAL --- */}
            {showDeleteModal && (
                <div className={styles.modalOverlay}>
                    <div className={styles.modalContainer}>
                        <h3 className={styles.modalTitle}>
                            {texts.are_you_sure || "Weet je het absoluut zeker?"}
                        </h3>
                        
                        {/* Updated this paragraph to use translations */}
                        <p className={styles.modalWarning}>
                            {texts.delete_modal_warning_p1 || "Deze actie kan"}{" "}
                            <strong>{texts.not || "niet"}</strong>{" "}
                            {texts.delete_modal_warning_p2 || "ongedaan worden gemaakt. Dit zal de club"}{" "}
                            <strong>{formData.name}</strong>{" "}
                            {texts.delete_modal_warning_p3 || "permanent verwijderen."}
                        </p>
                        
                        <div className={styles.modalConfirmBox}>
                            <label className={styles.formLabel}>
                                {/* Updated this label to use the dynamic replace logic */}
                                {(texts.type_to_confirm || "Typ {name} om te bevestigen:").replace("{name}", formData.name)}
                                <input 
                                    type="text" 
                                    className={styles.formInput}
                                    value={confirmName}
                                    onChange={(e) => setConfirmName(e.target.value)}
                                    placeholder={formData.name}
                                />
                            </label>
                        </div>

                        <div className={styles.modalActions}>
                            <button 
                                type="button" 
                                className={styles.cancelButton}
                                onClick={() => {
                                    setShowDeleteModal(false);
                                    setConfirmName("");
                                }}
                            >
                                {texts.cancel || "Annuleren"}
                            </button>
                            <button 
                                type="button" 
                                className={styles.confirmDeleteButton}
                                disabled={confirmName !== formData.name}
                                onClick={onConfirmDelete}
                            >
                                {texts.understand_delete || "Ik begrijp de gevolgen, verwijder club"}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default ClubGeneral;