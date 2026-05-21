// Team management UI component for DeletePlayerButton.

import commonStyles from "@/style/common/Common.module.css";
import formStyles   from "@/style/common/Forms.module.css";
import panelStyles  from "@/style/common/Panel.module.css";
import { useDeletePlayer } from "@/hooks/teams/useDeletePlayer.js";
import { Spinner }         from "@/components/forms/Spinner.jsx";
import { FormPanel }       from "@/components/forms/FormPanel.jsx";
import { FormPage }        from "@/components/forms/FormPage.jsx";
import teamStyles    from "@/style/TeamSettings.module.css";
import {TrashIcon} from "@/components/icon/TrashIcon.jsx";
import { useNavigate } from "react-router-dom";
import { useLangContext } from "@/context/useLangContext.jsx";
import { usePageTexts } from "@/hooks/common/usePageTexts.js";

/**
 * DeletePlayerButton - trash icon that opens a confirmation dropdown.
 * Supports 2-stage confirmation for minimum roster size violations.
 *
 * Props:
 *   teamId    {number|string}
 *   playerId  {number|string}  - the account/player id to remove
 *   onDeleted {() => void}     - called after successful deletion
 */
export default function DeletePlayerButton({ teamId, playerId, onDeleted }) {
    const { lang } = useLangContext();
    const navigate = useNavigate();
    const texts = usePageTexts("team_settings", lang);
    const {
        isOpen, openDialog, closeDialog,
        confirmDelete, loading, error,
        violateWarning, setViolateWarning,
    } = useDeletePlayer({ teamId, playerId, onDeleted });

    const getErrorMessage = (err) => {
        if (typeof err === "string") {
            const key = "team_settings.error_" + err.replace(/\s+/g, "_").toLowerCase();
            return texts[key] || err;
        }
        return err;
    };

    const handleConfirmViolate = () => {
        /*
         Confirms the delete after the minimum-roster warning appears.
        */
        if (violateWarning) {
            confirmDelete(true);
            setViolateWarning(null);
        }
    };

    const handleCreateNewTeam = () => {
        setViolateWarning(null);
        closeDialog();
        navigate("/dashboard?tab=teams");
    };

    return (
        <FormPanel
            title={texts.remove_player_title || "Remove Player"}
            triggerContent={<TrashIcon />}
            triggerClassName={teamStyles.deleteBtn}
            triggerOpenClassName={teamStyles.deleteBtnOpen}

            isOpen={isOpen}
            openPanel={openDialog}
            closePanel={closeDialog}

            step={0}
            totalSteps={1}
            onNext={null}
            onBack={null}
            onSubmit={violateWarning ? null : () => confirmDelete(false)}

            isLoading={loading}
            isSuccess={false}

            submitLabel={loading ? <><Spinner /> {texts.removing || "Removing..."}</> : (texts.remove_player_submit || "Remove")}
            canNext={!loading && !violateWarning}

            error={violateWarning ? null : error}
            errorMessage={violateWarning ? null : getErrorMessage(error)}

            panelClassName={teamStyles.confirmPanel}
            ariaLabel={texts.confirm_remove_player || "Confirm player removal"}
        >
            {/* --- Minimum roster violation warning dialog [NEW] ------- */}
            {violateWarning && (
                <FormPage active={true}>
                    <div className={`${commonStyles.alertBox} ${teamStyles.confirmWarning}`}>
                        <p className={commonStyles.warningText}>
                            {texts.remove_player_warn_violate || violateWarning.message}
                        </p>
                        <p className={commonStyles.secondaryText}>
                            {texts.remove_player_warn_action || "You can continue and remove this team from the ladder, or create a new team instead."}
                        </p>
                        {violateWarning.ladders && violateWarning.ladders.length > 0 && (
                            <div className={teamStyles.laddersList}>
                                <p className={commonStyles.secondaryText}>
                                    {texts.remove_player_warn_ladders || "Affected ladders:"}
                                </p>
                                <ul className={panelStyles.list}>
                                    {violateWarning.ladders.map(ladder => (
                                        <li key={ladder.id} className={teamStyles.ladderItem}>
                                            {ladder.name}
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}
                        <div className={teamStyles.confirmButtons}>
                            <button
                                className={`${formStyles.btn} ${formStyles.btnSecondary}`}
                                onClick={() => setViolateWarning(null)}
                            >
                                {texts.cancel_btn || "Cancel"}
                            </button>
                            <button
                                className={`${formStyles.btn} ${formStyles.btnSecondary}`}
                                onClick={handleCreateNewTeam}
                            >
                                {texts.create_new_team || "Create new team"}
                            </button>
                            <button
                                className={`${formStyles.btn} ${formStyles.btnPrimary}`}
                                onClick={handleConfirmViolate}
                                disabled={loading}
                            >
                                {loading ? <Spinner /> : (texts.remove_player_confirm_violate || "Remove Anyway")}
                            </button>
                        </div>
                    </div>
                </FormPage>
            )}

            {/* --- Page 0: confirmation [UNCHANGED] -------------------- */}
            {!violateWarning && (
                <FormPage active={true}>
                    <p className={teamStyles.confirmText}>
                        {texts.confirm_remove_player_text || "Are you sure you want to remove this player from the team?"}
                    </p>
                </FormPage>
            )}
        </FormPanel>
    );
}
