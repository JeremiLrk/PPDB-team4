import { FormPanel } from "@/components/forms/FormPanel.jsx";
import { FormPage }  from "@/components/forms/FormPage.jsx";
import { Field }     from "@/components/forms/Field.jsx";
import { PencilIcon } from "@/components/icon/PencilIcon.jsx";
import { useRenameTeam } from "@/hooks/teams/useRenameTeam.js";
import styles from "@/style/common/Forms.module.css";

/**
 * RenameTeamButton — pencil icon that opens a rename panel.
 *
 * Props:
 *   teamId      {number|string}
 *   currentName {string}
 *   onRenamed   {(team: object) => void}
 */
export default function RenameTeamButton({ teamId, currentName, onRenamed }) {
    const {
        newName, setNewName,
        step,
        openPanel, closePanel, submit,
        isOpen, isLoading, isSuccess, error,
    } = useRenameTeam({ teamId, currentName, onRenamed });

    const canSubmit = !!newName.trim();

    return (
        <FormPanel
            title="Rename Team"
            triggerContent={<PencilIcon />}

            isOpen={isOpen}
            openPanel={openPanel}
            closePanel={closePanel}

            step={step === -2 ? 0 : step}
            totalSteps={1}
            onNext={submit}
            onBack={undefined}
            onSubmit={submit}

            isLoading={isLoading}
            isSuccess={isSuccess}
            successLabel="Team renamed!"
            error={error}

            submitLabel="Rename"
            canNext={canSubmit}
        >
            <FormPage active={!isSuccess}>
                <Field label="New Name">
                    <input
                        className={styles.formInput}
                        type="text"
                        placeholder={currentName}
                        value={newName}
                        onChange={e => setNewName(e.target.value)}
                        onKeyDown={e => e.key === "Enter" && canSubmit && submit()}
                        disabled={isLoading}
                        autoFocus
                    />
                </Field>
            </FormPage>
        </FormPanel>
    );
}