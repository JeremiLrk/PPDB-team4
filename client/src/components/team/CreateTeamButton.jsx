import { FormPanel } from "@/components/forms/FormPanel.jsx";
import { FormPage }  from "@/components/forms/FormPage.jsx";
import { Field }     from "@/components/forms/Field.jsx";
import { PlusIcon }  from "@/components/icon/PlusIcon.jsx";
import { useCreateTeam } from "@/hooks/teams/useCreateTeam.js";
import { useSportTypes } from "@/hooks/useSportTypes.js";
import styles     from "@/style/common/Forms.module.css";


export default function CreateTeamButton({ clubs = [], onCreated }) {
    const {
        form, step,
        openForm, closeForm, updateField, submit,
        nextStep, prevStep,
        isOpen, isLoading, isSuccess, error,
    } = useCreateTeam({ onCreated });

    const { sportTypes, loading: sportTypesLoading } = useSportTypes();

    // Validation: "Next" is only available if the name is filled in
    const canNext = step === 0 ? !!form.name.trim() : true;

    return (
        <FormPanel
            title="Create Team"
            triggerContent={<><PlusIcon rotated={isOpen} /> New Team</>}

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
            successLabel="Team created!"
            error={error}

            submitLabel="Create Team"
            canNext={canNext}
        >
            <FormPage active={step === 0}>
                <Field label="Team Name *">
                    <input
                        className={styles.formInput}
                        type="text"
                        placeholder="e.g. Red Hawks"
                        value={form.name}
                        onChange={e => updateField("name", e.target.value)}
                        onKeyDown={e => e.key === "Enter" && canNext && nextStep()}
                        disabled={isLoading}
                        autoFocus
                    />
                </Field>

                {clubs.length > 0 && (
                    <Field label="Club (optional)">
                        <select
                            className={styles.formSelect}
                            value={form.clubId}
                            onChange={e => updateField("clubId", e.target.value)}
                            disabled={isLoading}
                        >
                            <option value="">- No club -</option>
                            {clubs.map(c => (
                                <option key={c.id} value={c.id}>{c.name}</option>
                            ))}
                        </select>
                    </Field>
                )}

                <Field label="Sport (optional)">
                    <select
                        className={styles.formSelect}
                        value={form.sportTypeId}
                        onChange={e => updateField("sportTypeId", e.target.value)}
                        disabled={isLoading || sportTypesLoading}
                    >
                        <option value="">
                            {sportTypesLoading ? "Loading…" : "- Any sport -"}
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
