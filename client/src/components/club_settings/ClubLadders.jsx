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
    onRemoveTeam,
    onDeleteLadder,
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
    const [ladderAction, setLadderAction] = useState(null);
    const [teamMessage, setTeamMessage] = useState(null);
    const showRuleSetField = supportsRuleSets;
    const selectedLadderId = teamForm.ladder_id ? Number(teamForm.ladder_id) : null;
    const selectedTeamId = teamForm.team_id ? Number(teamForm.team_id) : null;
    const selectedTeam = eligibleTeams.find((team) => Number(team.id) === selectedTeamId) || null;
    const selectedTeamLadderIds = Array.isArray(selectedTeam?.ladderIds) ? selectedTeam.ladderIds.map(Number) : [];
    const selectedTeamAlreadyInLadder = selectedLadderId ? selectedTeamLadderIds.includes(selectedLadderId) : false;
    const selectedTeamPendingInvite = selectedTeam?.pendingClubInvitation || null;
    const selectedTeamNeedsInvite = selectedTeam?.requiresInvite || selectedTeam?.membershipStatus === "independent";
    const selectedTeamHasManagers = Number(selectedTeam?.managerCount || 0) > 0;
    const addTeamDisabled = (
        addingTeam
        || !teamForm.ladder_id
        || !teamForm.team_id
        || selectedTeamAlreadyInLadder
        || Boolean(selectedTeamPendingInvite)
        || (selectedTeamNeedsInvite && !selectedTeamHasManagers)
    );
    const teamsByLadder = ladders.reduce((acc, ladder) => {
        acc[ladder.id] = eligibleTeams
            .filter((team) => Array.isArray(team.ladderIds) && team.ladderIds.map(Number).includes(Number(ladder.id)))
            .sort((a, b) => String(a.name || "").localeCompare(String(b.name || "")));
        return acc;
    }, {});

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
            const result = await onAddTeam(Number(teamForm.ladder_id), Number(teamForm.team_id));
            setTeamMessage({
                type: "success",
                text: result?.action === "invitation_sent"
                    ? (texts.team_invitation_sent || "Invitation sent to the team manager.")
                    : (texts.team_added_to_ladder || "Team added to ladder."),
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

    const handleRemoveTeam = async (ladderId, teamId, teamName) => {
        /*
         Removes one team from one ladder after confirmation.
        */
        if (typeof onRemoveTeam !== "function") return;
        const confirmed = window.confirm(
            texts.confirm_remove_team_from_ladder
            || `Remove ${teamName || "this team"} from this ladder? Unplayed matches for this team in this ladder will be cancelled.`
        );
        if (!confirmed) return;

        setLadderAction(`remove-${ladderId}-${teamId}`);
        setTeamMessage(null);
        try {
            const result = await onRemoveTeam(Number(ladderId), Number(teamId));
            setTeamMessage({
                type: "success",
                text: result?.cancelledMatches
                    ? (texts.team_removed_matches_cancelled || `Team removed. ${result.cancelledMatches} unplayed match(es) cancelled.`)
                    : (texts.team_removed_from_ladder || "Team removed from ladder."),
            });
        } catch (error) {
            setTeamMessage({
                type: "error",
                text: error?.message || texts.could_not_remove_team_from_ladder || "Could not remove team from ladder.",
            });
        } finally {
            setLadderAction(null);
        }
    };

    const handleDeleteLadder = async (ladderId, ladderName) => {
        /*
         Deletes one ladder after confirmation.
        */
        if (typeof onDeleteLadder !== "function") return;
        const confirmed = window.confirm(
            texts.confirm_delete_ladder
            || `Delete ${ladderName || "this ladder"}? Teams will be removed from this ladder, but existing match history is kept.`
        );
        if (!confirmed) return;

        setLadderAction(`delete-${ladderId}`);
        setTeamMessage(null);
        try {
            await onDeleteLadder(Number(ladderId));
            if (Number(teamForm.ladder_id) === Number(ladderId)) {
                setTeamForm((prev) => ({ ...prev, ladder_id: "" }));
            }
            setTeamMessage({
                type: "success",
                text: texts.ladder_deleted || "Ladder deleted.",
            });
        } catch (error) {
            setTeamMessage({
                type: "error",
                text: error?.message || texts.could_not_delete_ladder || "Could not delete ladder.",
            });
        } finally {
            setLadderAction(null);
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
                                    {team.membershipStatus === "independent" ? " - invite required" : " - club team"}
                                    {Array.isArray(team.ladderIds) && selectedLadderId && team.ladderIds.map(Number).includes(selectedLadderId) ? " - already in ladder" : ""}
                                    {team.pendingClubInvitation ? " - invite pending" : ""}
                                </option>
                            ))}
                        </select>

                        {selectedTeam ? (
                            <div className={styles.formMetaBox}>
                                <p className={styles.primaryText}>
                                    {selectedTeam.name}
                                </p>
                                <p className={styles.secondaryText}>
                                    {selectedTeamAlreadyInLadder
                                        ? (texts.team_already_in_ladder || "This team is already in the selected ladder.")
                                        : selectedTeamPendingInvite
                                            ? (texts.team_invite_pending || "This team already has a pending club invitation.")
                                            : selectedTeamNeedsInvite
                                                ? (texts.team_needs_invite || "This independent team needs manager approval before it can join the club and ladder.")
                                                : (texts.team_can_add_directly || "This club team can be added directly.")}
                                </p>
                                <p className={styles.secondaryText}>
                                    {(texts.team_managers_label || "Managers")}: {
                                        selectedTeam.managers?.length
                                            ? selectedTeam.managers.map((manager) => manager.name).join(", ")
                                            : (texts.no_team_managers || "No team managers")
                                    }
                                </p>
                                <p className={styles.secondaryText}>
                                    {(texts.team_players_label || "Players")}: {
                                        selectedTeam.players?.length
                                            ? selectedTeam.players.map((player) => player.name).join(", ")
                                            : (texts.no_team_players || "No players")
                                    }
                                </p>
                            </div>
                        ) : null}

                        <button
                            className={styles.submitButton}
                            type="submit"
                            disabled={addTeamDisabled}
                        >
                            {addingTeam
                                ? (texts.adding_team || "Toevoegen...")
                                : selectedTeamNeedsInvite
                                    ? (texts.invite_team || "Invite team")
                                    : (texts.add_team || "Team toevoegen")}
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
                                <div className={styles.ladderManageBlock}>
                                    <div>
                                    <p className={styles.primaryText}>{ladder.name}</p>
                                    <p className={styles.secondaryText}>
                                        {ladder.description || texts.no_ladder_description || "Geen omschrijving"}
                                    </p>
                                        <p className={styles.secondaryText}>
                                            {(texts.teams_in_ladder || "Teams in ladder")}: {(teamsByLadder[ladder.id] || []).length}
                                        </p>
                                    </div>

                                    <button
                                        type="button"
                                        className={styles.deleteButton}
                                        onClick={() => handleDeleteLadder(ladder.id, ladder.name)}
                                        disabled={ladderAction === `delete-${ladder.id}`}
                                    >
                                        {ladderAction === `delete-${ladder.id}`
                                            ? (texts.deleting || "Deleting...")
                                            : (texts.delete_ladder || "Delete ladder")}
                                    </button>

                                    {(teamsByLadder[ladder.id] || []).length > 0 ? (
                                        <ul className={styles.nestedList}>
                                            {teamsByLadder[ladder.id].map((team) => (
                                                <li key={team.id} className={styles.nestedListItem}>
                                                    <div>
                                                        <p className={styles.primaryText}>{team.name}</p>
                                                        <p className={styles.secondaryText}>
                                                            {(texts.team_players_label || "Players")}: {team.playerCount || 0}
                                                            {" · "}
                                                            {(texts.team_managers_label || "Managers")}: {team.managerCount || 0}
                                                        </p>
                                                    </div>
                                                    <button
                                                        type="button"
                                                        className={styles.deleteButton}
                                                        onClick={() => handleRemoveTeam(ladder.id, team.id, team.name)}
                                                        disabled={ladderAction === `remove-${ladder.id}-${team.id}`}
                                                    >
                                                        {ladderAction === `remove-${ladder.id}-${team.id}`
                                                            ? (texts.removing || "Removing...")
                                                            : (texts.remove_from_ladder || "Remove")}
                                                    </button>
                                                </li>
                                            ))}
                                        </ul>
                                    ) : (
                                        <p className={styles.muted}>
                                            {texts.no_teams_in_ladder || "No teams in this ladder yet."}
                                        </p>
                                    )}
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
