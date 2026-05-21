// Team management UI component for RenameTeamButton.

import { FormPanel } from "@/components/forms/FormPanel.jsx";
import { FormPage }  from "@/components/forms/FormPage.jsx";
import { Field }     from "@/components/forms/Field.jsx";
import { PencilIcon } from "@/components/icon/PencilIcon.jsx";
import { useRenameTeam } from "@/hooks/teams/useRenameTeam.js";
import styles from "@/style/common/Forms.module.css";
import { useLangContext } from "@/context/useLangContext.jsx";
import { usePageTexts } from "@/hooks/common/usePageTexts.js";
import { useThemeContext } from "@/context/useThemeContext.jsx";

/**
 * RenameTeamButton — pencil icon that opens a rename panel.
 *
 * Props:
 *   teamId      {number|string}
 *   currentName {string}
 *   onRenamed   {(team: object) => void}
 */
export default function RenameTeamButton({ teamId, currentName, onRenamed, theme: providedTheme }) {
    const { lang } = useLangContext();
    const { theme: contextTheme } = useThemeContext();
    const theme = providedTheme || contextTheme;
    const texts = usePageTexts("team_settings", lang);
    const {
        newName, setNewName,
        step,
        openPanel, closePanel, submit,
        isOpen, isLoading, isSuccess, error,
    } = useRenameTeam({ teamId, currentName, onRenamed });

    const canSubmit = !!newName.trim();
    /*
     Renders the rename-team confirmation flow.
    */

    return (
        <FormPanel
            title={texts.rename_team_title || "Rename Team"}
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
            successLabel={texts.rename_team_success || "Team renamed!"}
            error={error}

            submitLabel={texts.rename_team_submit || "Rename"}
            canNext={canSubmit}
            theme={theme}
        >
            <FormPage active={!isSuccess}>
                <Field label={texts.rename_team_new_name || "New Name"}>
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
