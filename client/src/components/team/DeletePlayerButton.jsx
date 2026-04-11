import { useDeletePlayer } from "@/hooks/teams/useDeletePlayer.js";
import { Spinner }         from "@/components/forms/Spinner.jsx";
import { FormPanel }       from "@/components/forms/FormPanel.jsx";
import { FormPage }        from "@/components/forms/FormPage.jsx";
import teamStyles    from "@/style/TeamSettings.module.css";

/**
 * DeletePlayerButton - trash icon that opens a confirmation dropdown.
 *
 * Props:
 *   teamId    {number|string}
 *   playerId  {number|string}  - the account/player id to remove
 *   onDeleted {() => void}     - called after successful deletion
 */
export default function DeletePlayerButton({ teamId, playerId, onDeleted }) {
    const {
        isOpen, openDialog, closeDialog,
        confirmDelete, loading, error,
    } = useDeletePlayer({ teamId, playerId, onDeleted });

    return (
        <FormPanel
            title="Remove Player"
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
            ariaLabel="Confirm player removal"
        >
            {/* --- Page 0: confirmation ------------------------------- */}
            <FormPage active={true}>
                <p className={teamStyles.confirmText}>
                    Are you sure you want to remove this player from the team?
                </p>
            </FormPage>
        </FormPanel>
    );
}
