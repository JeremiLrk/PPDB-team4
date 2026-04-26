import { useDeletePlayer } from "@/hooks/teams/useDeletePlayer.js";
import { Spinner }         from "@/components/forms/Spinner.jsx";
import { FormPanel }       from "@/components/forms/FormPanel.jsx";
import { FormPage }        from "@/components/forms/FormPage.jsx";
import teamStyles    from "@/style/TeamSettings.module.css";
import {TrashIcon} from "@/components/icon/TrashIcon.jsx";
import { useLangContext } from "@/context/useLangContext.jsx";
import { usePageTexts } from "@/hooks/common/usePageTexts.js";

/**
 * DeletePlayerButton - trash icon that opens a confirmation dropdown.
 *
 * Props:
 *   teamId    {number|string}
 *   playerId  {number|string}  - the account/player id to remove
 *   onDeleted {() => void}     - called after successful deletion
 */
export default function DeletePlayerButton({ teamId, playerId, onDeleted }) {
    const { lang } = useLangContext();
    const texts = usePageTexts("team_settings", lang);
    const {
        isOpen, openDialog, closeDialog,
        confirmDelete, loading, error,
    } = useDeletePlayer({ teamId, playerId, onDeleted });

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
            onSubmit={confirmDelete}

            isLoading={loading}
            isSuccess={false}

            submitLabel={loading ? <><Spinner /> {texts.removing || "Removing…"}</> : (texts.remove_player_submit || "Remove")}
            canNext={!loading}

            error={error}

            panelClassName={teamStyles.confirmPanel}
            ariaLabel={texts.confirm_remove_player || "Confirm player removal"}
        >
            {/* --- Page 0: confirmation ------------------------------- */}
            <FormPage active={true}>
                <p className={teamStyles.confirmText}>
                    {texts.confirm_remove_player_text || "Are you sure you want to remove this player from the team?"}
                </p>
            </FormPage>
        </FormPanel>
    );
}
