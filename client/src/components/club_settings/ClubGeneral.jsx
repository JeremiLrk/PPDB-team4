// Club settings UI component for ClubGeneral.

import { useState } from "react";
import styles from "@/style/ClubSettings.module.css";
import CityAutocompleteField from "@/components/common/CityAutocompleteField.jsx";

export function ClubGeneral({
    formData,
    onChange,
    onCitySelect,
    onSubmit,
    updating,
    updateMessage,
    sportTypes = [],
    handleDeleteClub,
    texts = {},
}) {
    /*
     Owns the general club settings form and delete modal.
    */
    const [showDeleteModal, setShowDeleteModal] = useState(false);
    const [confirmName, setConfirmName] = useState("");

    const canDelete = typeof handleDeleteClub === "function";

    function closeDeleteModal() {
        /*
         Closes the delete confirmation modal and clears the draft name.
        */
        setShowDeleteModal(false);
        setConfirmName("");
    }

    function confirmDelete() {
        /*
         Deletes the club only when the typed confirmation matches.
        */
        if (!canDelete || confirmName !== (formData.name || "")) {
            return;
        }
        handleDeleteClub();
        closeDeleteModal();
    }

    return (
        <div className={styles.contentFade}>
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
                        <CityAutocompleteField
                            value={formData.city || ""}
                            onChange={onChange}
                            onSelect={onCitySelect}
                            placeholder={texts.city_placeholder || "Stad waar je club gevestigd is"}
                            required
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

            {canDelete && (
                <div className={styles.formActions} style={{ marginTop: "1rem" }}>
                    <button
                        type="button"
                        className={styles.deleteButton}
                        onClick={() => setShowDeleteModal(true)}
                    >
                        {texts.delete_club || "Club Verwijderen"}
                    </button>
                </div>
            )}
        </article>

        {showDeleteModal && canDelete && (
            <div className={styles.modalOverlay}>
                <div className={styles.modalContainer}>
                    <h3 className={styles.modalTitle}>
                        {texts.delete_modal_title || "Weet je het absoluut zeker?"}
                    </h3>

                    <p className={styles.modalWarning}>
                        {(texts.delete_modal_warning || "This action cannot be undone. This will permanently delete {name}.").replace(
                            "{name}",
                            formData.name || "",
                        )}
                    </p>

                    <div className={styles.modalConfirmBox}>
                        <label className={styles.formLabel}>
                            {(texts.type_to_confirm || "Typ {name} om te bevestigen:").replace("{name}", formData.name || "")}
                            <input
                                type="text"
                                className={styles.formInput}
                                value={confirmName}
                                onChange={(event) => setConfirmName(event.target.value)}
                                placeholder={formData.name || ""}
                            />
                        </label>
                    </div>

                    <div className={styles.modalActions}>
                        <button
                            type="button"
                            className={styles.cancelButton}
                            onClick={closeDeleteModal}
                        >
                            {texts.cancel || "Annuleren"}
                        </button>
                        <button
                            type="button"
                            className={styles.confirmDeleteButton}
                            disabled={confirmName !== (formData.name || "")}
                            onClick={confirmDelete}
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
