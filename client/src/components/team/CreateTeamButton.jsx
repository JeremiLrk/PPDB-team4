// Team management UI component for CreateTeamButton.

import { FormPanel } from "@/components/forms/FormPanel.jsx";
import { FormPage }  from "@/components/forms/FormPage.jsx";
import { Field }     from "@/components/forms/Field.jsx";
import { PlusIcon }  from "@/components/icon/PlusIcon.jsx";
import { useCreateTeam } from "@/hooks/teams/useCreateTeam.js";
import { useSportTypes } from "@/hooks/useSportTypes.js";
import { useCurrentUserContext } from "@/context/useCurrentUserContext.jsx";
import commonStyles from "@/style/common/Common.module.css";
import styles     from "@/style/common/Forms.module.css";
import buttonStyles from "@/style/common/Buttons.module.css";
import { useLangContext } from "@/context/useLangContext.jsx";
import { usePageTexts } from "@/hooks/common/usePageTexts.js";


export default function CreateTeamButton({ clubs = [], onCreated, theme, texts: providedTexts }) {
    const { lang } = useLangContext();
    const { currentUser } = useCurrentUserContext();
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

    async function addCurrentUserAsPlayer(team) {
        /*
         Adds the logged-in account to the freshly created team, then accepts
         the generated join request so the user lands in the team immediately.
        */
        if (!form.addSelfAsPlayer) {
            return;
        }
        if (!team?.id || !currentUser?.id) {
            throw new Error(texts.self_add_failed || "Could not add yourself as a player.");
        }

        const addResponse = await fetch(`/api/teams/${team.id}/players`, {
            method: "POST",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ accountId: currentUser.id }),
        });

        const addData = await addResponse.json().catch(() => ({}));

        if (addResponse.status === 202 && addData?.warning === "exceeds_max_players") {
            throw new Error(addData?.message || texts.self_add_warning || "Adding yourself would exceed the ladder roster limit.");
        }

        if (!addResponse.ok) {
            throw new Error(addData?.message || texts.self_add_failed || "Could not add yourself as a player.");
        }

        const requestId = addData?.request?.id;
        if (!requestId) {
            throw new Error(texts.self_add_missing_request || "Missing join request for self-add.");
        }

        const acceptResponse = await fetch(
            `/api/teams/${team.id}/players/join-requests/${requestId}/accept`,
            {
                method: "POST",
                credentials: "include",
            },
        );

        const acceptData = await acceptResponse.json().catch(() => ({}));
        if (!acceptResponse.ok) {
            throw new Error(acceptData?.message || texts.self_add_failed || "Could not finalize your player membership.");
        }

    }

    async function handleSubmit() {
        /*
         Submits the team and optionally runs the self-add follow-up in the same
         wizard so the dashboard does not need a separate post-create card.
        */
        await submit({
            afterCreated: addCurrentUserAsPlayer,
        });
    }

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
            onSubmit={handleSubmit}

            isLoading={isLoading}
            isSuccess={isSuccess}
            successLabel={
                form.addSelfAsPlayer
                    ? (texts.team_created_and_self_added || texts.team_created || "Team created!")
                    : (texts.team_created || "Team created!")
            }
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

                <label className={styles.formLabel} style={{ gap: "0.3rem", cursor: "pointer" }}>
                    <span style={{ display: "flex", alignItems: "center", gap: "0.55rem" }}>
                        <input
                            type="checkbox"
                            checked={form.addSelfAsPlayer}
                            aria-label={texts.add_self_as_player || "Add yourself as player"}
                            onChange={e => updateField("addSelfAsPlayer", e.target.checked)}
                            disabled={isLoading}
                            style={{ accentColor: theme === "light" ? "#0ea5e9" : "#38bdf8", width: "1rem", height: "1rem" }}
                        />
                        <span className={commonStyles.primaryText} style={{ fontWeight: 600 }}>
                            {texts.add_self_as_player || "Add yourself as a player"}
                        </span>
                    </span>
                </label>
            </FormPage>
        </FormPanel>
    );
}
