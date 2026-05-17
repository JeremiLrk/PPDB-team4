// Team management UI component for CreateTeamButton.

import { FormPanel } from "@/components/forms/FormPanel.jsx";
import { FormPage }  from "@/components/forms/FormPage.jsx";
import { Field }     from "@/components/forms/Field.jsx";
import { PlusIcon }  from "@/components/icon/PlusIcon.jsx";
import { useCreateTeam } from "@/hooks/teams/useCreateTeam.js";
import { useSportTypes } from "@/hooks/useSportTypes.js";
import styles     from "@/style/common/Forms.module.css";
import buttonStyles from "@/style/common/Buttons.module.css";
import { useLangContext } from "@/context/useLangContext.jsx";
import { usePageTexts } from "@/hooks/common/usePageTexts.js";


export default function CreateTeamButton({ clubs = [], onCreated, theme, texts: providedTexts }) {
    const { lang } = useLangContext();
    const fallbackTexts = usePageTexts("dashboard", lang);
    const {
        form, step,
        openForm, closeForm, updateField, submit,
        nextStep, prevStep,
        isOpen, isLoading, isSuccess, error,
    } = useCreateTeam({ onCreated });

    const { sportTypes, loading: sportTypesLoading } = useSportTypes();
    const texts = { ...fallbackTexts, ...(providedTexts || {}) };

    const canNext = step === 0 ? !!form.name.trim() : true;
    /*
     Keeps the forward action disabled until the first-step name is filled in.
    */

    return (
        <FormPanel
            title={texts.create_team_title || "Create Team"}
            triggerContent={<><PlusIcon rotated={isOpen} /> {texts.new_team || "New Team"}</>}
            triggerClassName={buttonStyles.createTeamTrigger}
            triggerOpenClassName={buttonStyles.createTeamTriggerOpen}
            panelClassName={buttonStyles.createTeamPanel}
            theme={theme}

            isOpen={isOpen}
            openPanel={openForm}
            closePanel={closeForm}

            step={step}
            totalSteps={1}
            onNext={nextStep}
            onBack={prevStep}
            onSubmit={submit}

            isLoading={isLoading}
            isSuccess={isSuccess}
            successLabel={texts.team_created || "Team created!"}
            error={error}

            submitLabel={texts.create_team || "Create Team"}
            canNext={canNext}
        >
            <FormPage active={step === 0}>
                <Field label={texts.team_name || "Team Name *"}>
                    <input
                        className={styles.formInput}
                        type="text"
                        placeholder={texts.team_name_placeholder || "e.g. Red Hawks"}
                        value={form.name}
                        onChange={e => updateField("name", e.target.value)}
                        onKeyDown={e => e.key === "Enter" && canNext && nextStep()}
                        disabled={isLoading}
                        autoFocus
                    />
                </Field>

                {clubs.length > 0 && (
                    <Field label={texts.club_optional || "Club (optional)"}>
                        <select
                            className={styles.formSelect}
                            value={form.clubId}
                            onChange={e => updateField("clubId", e.target.value)}
                            disabled={isLoading}
                        >
                            <option value="">{texts.no_club || "- No club -"}</option>
                            {clubs.map(c => (
                                <option key={c.id} value={c.id}>{c.name}</option>
                            ))}
                        </select>
                    </Field>
                )}

                <Field label={texts.sport_optional || "Sport (optional)"}>
                    <select
                        className={styles.formSelect}
                        value={form.sportTypeId}
                        onChange={e => updateField("sportTypeId", e.target.value)}
                        disabled={isLoading || sportTypesLoading}
                    >
                        <option value="">
                            {sportTypesLoading ? (texts.loading_sport || "Loading…") : (texts.any_sport || "- Any sport -")}
                        </option>
                        {sportTypes.map(s => (
                            <option key={s.id} value={s.id}>{s.name}</option>
                        ))}
                    </select>
                </Field>
            </FormPage>
        </FormPanel>
    );
}
