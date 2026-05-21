// Club settings UI component for ClubLadders.

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
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
    const navigate = useNavigate();
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
    const selectedLadder = ladders.find((ladder) => Number(ladder.id) === selectedLadderId) || null;
    const selectedLadderRuleSet = ruleSets.find((ruleSet) => Number(ruleSet.id) === Number(selectedLadder?.ruleset_id)) || null;
    const selectedLadderSport = sportTypes.find((sport) => Number(sport.id) === Number(selectedLadder?.sport_type_id)) || null;
    const selectedTeamSportId = Number(selectedTeam?.sportTypeId || selectedTeam?.sport_type_id || 0) || null;
    const selectedTeamSportName = selectedTeam?.sportName || selectedTeam?.sport_name || null;
    const selectedLadderExpectedPlayers = (() => {
        if (selectedLadderRuleSet?.gameFormat === "singles") return 1;
        if (selectedLadderRuleSet?.gameFormat === "doubles") return 2;
        return Number(selectedLadderSport?.maxPlayers || 0);
    })();
    const selectedTeamPlayerCount = Number(selectedTeam?.playerCount || 0);
    const selectedTeamTooLargeForLadder = Boolean(selectedLadderExpectedPlayers) && selectedTeamPlayerCount > selectedLadderExpectedPlayers;
    const selectedTeamSportMismatch = Boolean(
        selectedLadderSport?.id
        && selectedTeamSportId
        && Number(selectedLadderSport.id) !== Number(selectedTeamSportId)
    );
    const addTeamDisabled = (
        addingTeam
        || !teamForm.ladder_id
        || !teamForm.team_id
        || selectedTeamAlreadyInLadder
    );
    const teamsByLadder = ladders.reduce((acc, ladder) => {
        acc[ladder.id] = eligibleTeams
            .filter((team) => Array.isArray(team.ladderIds) && team.ladderIds.map(Number).includes(Number(ladder.id)))
            .sort((a, b) => String(a.name || "").localeCompare(String(b.name || "")));
        return acc;
    }, {});
    const clubTeams = eligibleTeams
        .filter((team) => team.membershipStatus !== "independent")
        .sort((a, b) => String(a.name || "").localeCompare(String(b.name || "")));
    const independentTeams = eligibleTeams
        .filter((team) => team.membershipStatus === "independent")
        .sort((a, b) => String(a.name || "").localeCompare(String(b.name || "")));

    function formatTeamOption(team) {
        /*
         Shows the team name together with its roster size in the selector.
        */
        const count = Number(team.playerCount || 0);
        if (!count) {
            return team.name;
        }

        const label = count === 1
            ? (texts.team_player_short || "player")
            : (texts.team_players_short || "players");

        return `${team.name} · ${count} ${label}`;
    }

    function formatExpectedPlayers(expectedPlayers) {
        if (!expectedPlayers) return null;
        const label = expectedPlayers === 1
            ? (texts.team_player_short || "player")
            : (texts.team_players_short || "players");
        return `${expectedPlayers} ${label}`;
    }

    function formatRuleSetName(ruleSet) {
        if (!ruleSet) return texts.no_ruleset || "None";
        return ruleSet.name || texts.no_ruleset || "None";
    }

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
            const result = await onAddTeam(
                Number(teamForm.ladder_id),
                Number(teamForm.team_id),
                selectedTeamTooLargeForLadder,
                selectedTeamSportMismatch,
            );
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
                                <optgroup label={texts.teams_from_your_club || "Teams from your club"}>
                                    {clubTeams.map((team) => (
                                        <option key={team.id} value={team.id}>
                                            {formatTeamOption(team)}
                                            {Array.isArray(team.ladderIds) && selectedLadderId && team.ladderIds.map(Number).includes(selectedLadderId) ? " - already in ladder" : ""}
                                        </option>
                                    ))}
                                </optgroup>
                                <optgroup label={texts.independent_teams || "Independent teams"}>
                                    {independentTeams.map((team) => (
                                        <option key={team.id} value={team.id}>
                                            {formatTeamOption(team)}
                                            {team.pendingClubInvitation ? " - invite pending" : " - invite needed"}
                                        </option>
                                    ))}
                                </optgroup>
                            </select>

                            <p className={styles.secondaryText}>
                                {texts.team_group_hint || "Club teams can be added directly. Independent teams need an invite first. Ladder team size limits are shown for the selected ladder."}
                            </p>

                            {selectedLadderExpectedPlayers ? (
                                <p className={styles.secondaryText}>
                                    {texts.ladder_team_size_hint || `This ladder expects teams of up to ${formatExpectedPlayers(selectedLadderExpectedPlayers)}.`}
                                </p>
                            ) : null}

                            {selectedLadderExpectedPlayers === 1 ? (
                                <button
                                    type="button"
                                    className={styles.primaryButton}
                                    onClick={() => navigate("/dashboard?tab=teams")}
                                >
                                    {texts.create_one_player_team || "Create a team first"}
                                </button>
                            ) : null}

                            {selectedTeam ? (
                                <div className={styles.formMetaBox}>
                                    <p className={styles.primaryText}>
                                        {selectedTeam.name}
                                    </p>
                                    <p className={styles.secondaryText}>
                                        {selectedTeamTooLargeForLadder
                                            ? (texts.team_too_large_for_ladder || `This team has ${selectedTeamPlayerCount} players, but the selected ladder expects teams of at most ${selectedLadderExpectedPlayers}.`)
                                            : selectedTeamSportMismatch
                                            ? (texts.team_sport_mismatch_warning_body || `This team is ${selectedTeamSportName || "a different sport"}, but this ladder expects ${selectedLadderSport?.name || "another sport"}. Accepting will change the team's sport type to match the ladder.`)
                                            : selectedTeamAlreadyInLadder
                                            ? (texts.team_already_in_ladder || "This team is already in the selected ladder.")
                                            : selectedTeamPendingInvite
                                                ? (texts.team_invite_pending || "This team already has a pending club invitation.")
                                                : selectedTeamNeedsInvite
                                                    ? (texts.team_needs_invite || "This independent team needs manager approval before it can join the club and ladder.")
                                            : (texts.team_can_add_directly || "This club team can be added directly.")}
                                    </p>
                                    {selectedTeamTooLargeForLadder ? (
                                        <p className={styles.warning} style={{ marginTop: "0.55rem" }}>
                                            {texts.team_size_warning_title || "Team size warning"}: {texts.team_size_warning_body || `This team has ${selectedTeamPlayerCount} players, but this ladder expects teams of at most ${selectedLadderExpectedPlayers}. You can still add it, or create a new team instead.`}
                                        </p>
                                    ) : selectedTeamSportMismatch ? (
                                        <p className={styles.warning} style={{ marginTop: "0.55rem" }}>
                                            {texts.team_sport_mismatch_warning_title || "Team sport warning"}: {texts.team_sport_mismatch_warning_body || `This team is ${selectedTeamSportName || "a different sport"}, but this ladder expects ${selectedLadderSport?.name || "another sport"}. Accepting will change the team's sport type to match the ladder.`}
                                        </p>
                                    ) : null}
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
                                    <p className={styles.secondaryText}>
                                        {(texts.ruleset_label || "Rule set")}: {formatRuleSetName(selectedLadderRuleSet)}
                                    </p>
                                    {selectedLadderExpectedPlayers && !selectedTeamTooLargeForLadder ? (
                                        <p className={styles.secondaryText}>
                                            {texts.team_fits_ladder_format || "This team fits the selected ladder format."}
                                        </p>
                                    ) : null}
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

            <article className={`${styles.panel} ${styles.panelScroll}`}>
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
                                        {(texts.ruleset_label || "Rule set")}: {formatRuleSetName(ruleSets.find((ruleSet) => Number(ruleSet.id) === Number(ladder.ruleset_id)))}
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
