// Club settings UI component for ClubLadders.

import { useEffect, useState } from "react";
import { useSportTypes } from "@/hooks/useSportTypes";
import styles from "@/style/ClubSettings.module.css";

export function ClubLadders({
    ladders = [],
    onCreate,
    ratingFunctions = [],
    ruleSets = [],
    eligibleTeams = [],
    onAddTeam,
    supportsRuleSets = true,
    texts = {},
}) {
    const { sportTypes } = useSportTypes();
    /*
     Owns the ladder creation form and ladder-team linking form.
    */

    const [form, setForm] = useState({
        name: "",
        description: "",
        sport_type_id: "",
        rule_set_id: "",
        ladder_rating_function_id: "",
    });

    const [teamForm, setTeamForm] = useState({
        ladder_id: "",
        team_id: "",
    });

    const [submitting, setSubmitting] = useState(false);
    const [addingTeam, setAddingTeam] = useState(false);
    const [teamMessage, setTeamMessage] = useState(null);
    const showRuleSetField = supportsRuleSets;

    useEffect(() => {
        if (!showRuleSetField && form.rule_set_id) {
            setForm((prev) => ({
                ...prev,
                rule_set_id: "",
            }));
        }
    }, [form.rule_set_id, showRuleSetField]);

    const handleChange = (event) => {
        /*
         Updates one field in the ladder creation form.
        */
        const { name, value } = event.target;
        setForm((prev) => ({
            ...prev,
            [name]: value,
        }));
    };

    const handleTeamChange = (event) => {
        /*
         Updates one field in the ladder-team linking form.
        */
        const { name, value } = event.target;
        setTeamForm((prev) => ({
            ...prev,
            [name]: value,
        }));
    };
    const handleCreate = async () => {
        /*
         Creates a new ladder after validating the required fields.
        */
        if (
            !form.name.trim()
            || !form.sport_type_id
            || !form.ladder_rating_function_id
            || (showRuleSetField && !form.rule_set_id)
        ) {
            alert(texts.fill_all_required_fields || "Vul alle verplichte velden in.");
            return;
        }

        setSubmitting(true);
        try {
            await onCreate({
                ...form,
                sport_type_id: Number(form.sport_type_id),
                ruleset_id: showRuleSetField && form.rule_set_id ? Number(form.rule_set_id) : null,
                ladder_rating_function_id: Number(form.ladder_rating_function_id),
            });
            setForm({
                name: "",
                description: "",
                sport_type_id: "",
                rule_set_id: "",
                ladder_rating_function_id: "",
            });
        } finally {
            setSubmitting(false);
        }
    };

    const handleAddTeam = async (event) => {
        /*
         Links one selected team to one selected ladder.
        */
        event.preventDefault();

        if (!teamForm.ladder_id || !teamForm.team_id) {
            setTeamMessage({
                type: "error",
                text: texts.select_ladder_and_team || "Select a ladder and a team.",
            });
            return;
        }

        if (typeof onAddTeam !== "function") {
            setTeamMessage({
                type: "error",
                text: texts.could_not_add_team_to_ladder || "Could not add team to ladder.",
            });
            return;
        }

        setAddingTeam(true);
        setTeamMessage(null);

        try {
            await onAddTeam(Number(teamForm.ladder_id), Number(teamForm.team_id));
            setTeamMessage({
                type: "success",
                text: texts.team_added_to_ladder || "Team added to ladder.",
            });
            setTeamForm({
                ladder_id: "",
                team_id: "",
            });
        } catch (error) {
            setTeamMessage({
                type: "error",
                text: error?.message || texts.could_not_add_team_to_ladder || "Could not add team to ladder.",
            });
        } finally {
            setAddingTeam(false);
        }
    };

    return (
        <div className={`${styles.contentGrid} ${styles.contentFade}`}>
            <div className={styles.profileStack}>
                <article className={styles.panel}>
                    <h3 className={styles.panelTitle}>{texts.ladder_create_title || "Ladder aanmaken"}</h3>

                    <div className={styles.form}>
                        <input
                            className={styles.formInput}
                            name="name"
                            placeholder={texts.ladder_name_placeholder || "Laddernaam"}
                            value={form.name}
                            onChange={handleChange}
                        />

                        <select className={styles.formInput} name="sport_type_id" value={form.sport_type_id} onChange={handleChange}>
                            <option value="" disabled>{texts.choose_sport_type || "Kies een sporttype"}</option>
                            {sportTypes.map((sport) => (
                                <option key={sport.id} value={sport.id}>{sport.name}</option>
                            ))}
                        </select>

                        {showRuleSetField ? (
                            <select className={styles.formInput} name="rule_set_id" value={form.rule_set_id} onChange={handleChange}>
                                <option value="" disabled>{texts.choose_rule_set || "Kies een regelset"}</option>
                                {ruleSets.map((ruleSet) => (
                                    <option key={ruleSet.id} value={ruleSet.id}>{ruleSet.name}</option>
                                ))}
                            </select>
                        ) : null}

                        <select className={styles.formInput} name="ladder_rating_function_id" value={form.ladder_rating_function_id} onChange={handleChange}>
                            <option value="" disabled>{texts.choose_rating_function || "Kies ratingsysteem"}</option>
                            {ratingFunctions.map((ratingFunction) => (
                                <option key={ratingFunction.id} value={ratingFunction.id}>{ratingFunction.name}</option>
                            ))}
                        </select>

                        <textarea
                            className={styles.formTextarea}
                            name="description"
                            placeholder={texts.ladder_description_placeholder || "Omschrijving"}
                            value={form.description}
                            onChange={handleChange}
                            rows={3}
                        />

                        <button
                            className={styles.submitButton}
                            type="button"
                            onClick={handleCreate}
                            disabled={submitting}
                        >
                            {submitting ? (texts.creating_ladder || "Aanmaken...") : (texts.create_ladder || "Ladder aanmaken")}
                        </button>
                    </div>
                </article>

                <article className={styles.panel}>
                    <h3 className={styles.panelTitle}>{texts.add_team_title || "Team toevoegen aan ladder"}</h3>

                    <form className={styles.form} onSubmit={handleAddTeam}>
                        <p className={styles.secondaryText}>
                            {texts.add_team_subtitle || "Select a ladder and a team to link them."}
                        </p>

                        <select
                            className={styles.formInput}
                            name="ladder_id"
                            value={teamForm.ladder_id}
                            onChange={handleTeamChange}
                        >
                            <option value="" disabled>
                                {texts.select_ladder || "Selecteer een ladder"}
                            </option>
                            {ladders.map((ladder) => (
                                <option key={ladder.id} value={ladder.id}>
                                    {ladder.name}
                                </option>
                            ))}
                        </select>

                        <select
                            className={styles.formInput}
                            name="team_id"
                            value={teamForm.team_id}
                            onChange={handleTeamChange}
                        >
                            <option value="" disabled>
                                {texts.select_team || "Selecteer een team"}
                            </option>
                            {eligibleTeams.map((team) => (
                                <option key={team.id} value={team.id}>
                                    {team.name}
                                </option>
                            ))}
                        </select>

                        <button
                            className={styles.submitButton}
                            type="submit"
                            disabled={addingTeam || !teamForm.ladder_id || !teamForm.team_id}
                        >
                            {addingTeam ? (texts.adding_team || "Toevoegen...") : (texts.add_team || "Team toevoegen")}
                        </button>

                        {teamMessage ? (
                            <p className={`${styles.notice} ${teamMessage.type === "error" ? styles.noticeError : styles.noticeSuccess}`}>
                                {teamMessage.text}
                            </p>
                        ) : null}
                    </form>
                </article>
            </div>

            <article className={styles.panel}>
                <h3 className={styles.panelTitle}>{texts.ladders_title || "Ladders"}</h3>

                {ladders.length === 0 ? (
                    <p className={styles.muted}>{texts.no_ladders || "Nog geen ladders."}</p>
                ) : (
                    <ul className={styles.list}>
                        {ladders.map((ladder) => (
                            <li key={ladder.id} className={styles.listItem}>
                                <div>
                                    <p className={styles.primaryText}>{ladder.name}</p>
                                    <p className={styles.secondaryText}>
                                        {ladder.description || texts.no_ladder_description || "Geen omschrijving"}
                                    </p>
                                </div>
                            </li>
                        ))}
                    </ul>
                )}
            </article>
        </div>
    );
}

export default ClubLadders;
