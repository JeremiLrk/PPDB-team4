import { useDeleteManager } from "@/hooks/teams/useDeleteManager.js";
import { Spinner }          from "@/components/forms/Spinner.jsx";
import { FormPanel }        from "@/components/forms/FormPanel.jsx";
import { FormPage }         from "@/components/forms/FormPage.jsx";
import { TrashIcon }        from "@/components/icon/TrashIcon.jsx";
import teamStyles           from "@/style/TeamSettings.module.css";
import { useLangContext } from "@/context/useLangContext.jsx";
import { usePageTexts } from "@/hooks/common/usePageTexts.js";

/**
 * DeleteManagerButton — a trash can with confirmation of manager deletion.
 *
 * Props:
 * teamId {number|string}
 * managerId {number|string} — manager account.id
 * onDeleted {() => void}
 */
export default function DeleteManagerButton({ teamId, managerId, onDeleted }) {
    const { lang } = useLangContext();
    const texts = usePageTexts("team_settings", lang);
    const {
        isOpen, openDialog, closeDialog,
        confirmDelete, loading, error,
    } = useDeleteManager({ teamId, managerId, onDeleted });

    return (
        <FormPanel
            title={texts.remove_manager_title || "Remove Manager"}
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

            submitLabel={loading ? <><Spinner /> {texts.removing || "Removing…"}</> : (texts.remove_manager_submit || "Remove")}
            canNext={!loading}

            error={error}

            panelClassName={teamStyles.confirmPanel}
            ariaLabel={texts.confirm_remove_manager || "Confirm manager removal"}
        >
            <FormPage active={true}>
                <p className={teamStyles.confirmText}>
                    {texts.confirm_remove_manager_text || "Are you sure you want to remove this manager from the team?"}
                </p>
            </FormPage>
        </FormPanel>
    );
}
