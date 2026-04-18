import { useDeleteManager } from "@/hooks/teams/useDeleteManager.js";
import { Spinner }          from "@/components/forms/Spinner.jsx";
import { FormPanel }        from "@/components/forms/FormPanel.jsx";
import { FormPage }         from "@/components/forms/FormPage.jsx";
import { TrashIcon }        from "@/components/icon/TrashIcon.jsx";
import teamStyles           from "@/style/TeamSettings.module.css";

/**
 * DeleteManagerButton — кошик з підтвердженням видалення менеджера.
 *
 * Props:
 *   teamId    {number|string}
 *   managerId {number|string}  — account.id менеджера
 *   onDeleted {() => void}
 */
export default function DeleteManagerButton({ teamId, managerId, onDeleted }) {
    const {
        isOpen, openDialog, closeDialog,
        confirmDelete, loading, error,
    } = useDeleteManager({ teamId, managerId, onDeleted });

    return (
        <FormPanel
            title="Remove Manager"
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

            submitLabel={loading ? <><Spinner /> Removing…</> : "Remove"}
            canNext={!loading}

            error={error}

            panelClassName={teamStyles.confirmPanel}
            ariaLabel="Confirm manager removal"
        >
            <FormPage active={true}>
                <p className={teamStyles.confirmText}>
                    Are you sure you want to remove this manager from the team?
                </p>
            </FormPage>
        </FormPanel>
    );
}
