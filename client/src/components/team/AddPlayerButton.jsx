// Team management UI component for AddPlayerButton.

import commonStyles from "@/style/common/Common.module.css";
import formStyles   from "@/style/common/Forms.module.css";
import panelStyles  from "@/style/common/Panel.module.css";
import teamStyles   from "@/style/TeamSettings.module.css";
import btnStyles  from "@/style/common/Buttons.module.css";

import { useAddPlayer } from "@/hooks/teams/useAddPlayer.js";
import { PlusIcon }     from "@/components/icon/PlusIcon.jsx";
import { Spinner }      from "@/components/forms/Spinner.jsx";
import { FormPanel }    from "@/components/forms/FormPanel.jsx";
import { FormPage }     from "@/components/forms/FormPage.jsx";
import ItemCard         from "@/components/common/ItemCard.jsx";
import { useNavigate }  from "react-router-dom";
import { useLangContext } from "@/context/useLangContext.jsx";
import { usePageTexts } from "@/hooks/common/usePageTexts.js";
import { useThemeContext } from "@/context/useThemeContext.jsx";

/**
 * AddPlayerButton - dropdown panel for searching and adding players to a team.
 *
 * Props:
 *   teamId    {number|string}  - the team to add players to
 *   onAdded   {() => void}     - called after a player is successfully added
 */
export default function AddPlayerButton({ teamId, onAdded, theme: providedTheme }) {
    /*
     Owns the search-and-add flow for team members.
    */
    const { lang } = useLangContext();
    const { theme: contextTheme } = useThemeContext();
    const navigate = useNavigate();
    const theme = providedTheme || contextTheme;
    const texts = usePageTexts("team_settings", lang);
    const {
        isOpen, openPanel, closePanel,
        query, setQuery,
        results, searching, searchErr,
        addPlayer, addingId, addedIds, addErr,
        confirmWarning, setConfirmWarning,
        inputRef,
    } = useAddPlayer({ teamId, onAdded });

    const getErrorMessage = (err) => {
        /*
         Converts backend error keys into localized copy.
        */
        if (typeof err === "string") {
            const key = "team_settings.error_" + err.replace(/\s+/g, "_").toLowerCase();
            return texts[key] || err;
        }
        return err;
    };

    const handleConfirmExceed = async () => {
        /*
         Confirms the add after the ladder warning appears.
        */
        if (confirmWarning) {
            await addPlayer(confirmWarning.accountId, true);
            setConfirmWarning(null);
        }
    };

    const handleCreateNewTeam = () => {
        setConfirmWarning(null);
        closePanel();
        navigate("/dashboard?tab=teams");
    };

    return (
        <FormPanel
            title={texts.add_player_title || "Add Player"}
            triggerContent={<><PlusIcon rotated={isOpen} /> {texts.add_player_btn || "Add Player"}</>}

            isOpen={isOpen}
            openPanel={openPanel}
            closePanel={closePanel}

            // One page - navigation hidden automatically
            step={0}
            totalSteps={1}
            onNext={null}
            onBack={null}
            onSubmit={closePanel}

            // No loading/success state at the panel level —
            // each result card has its own state
            isLoading={false}
            isSuccess={false}

            // The footer button simply dismisses the panel; the plus button in each row performs the add action.
            submitLabel={texts.confirm || "Confirm"}
            error={confirmWarning ? null : (addErr || searchErr || null)}
            errorMessage={confirmWarning ? null : getErrorMessage(addErr || searchErr)}

            panelClassName={teamStyles.addPlayerPanel}
            ariaLabel={texts.add_player_aria || "Add player to team"}
            theme={theme}

        >
            {/* --- Confirmation dialog for exceeding ladder limits ------- */}
            {confirmWarning && (
                <FormPage active={true}>
                    <div className={`${commonStyles.alertBox} ${teamStyles.confirmWarning}`}>
                        <p className={commonStyles.warningText}>
                            {texts.add_player_warn_exceed || confirmWarning.message}
                        </p>
                        <p className={commonStyles.secondaryText}>
                            {texts.add_player_warn_action || "You can continue and remove this team from the ladder, or create a new team instead."}
                        </p>
                        {confirmWarning.ladders && confirmWarning.ladders.length > 0 && (
                            <div className={teamStyles.laddersList}>
                                <p className={commonStyles.warningText}>
                                    {texts.add_player_warn_ladders || "Affected ladders:"}
                                </p>
                                <ul className={panelStyles.list}>
                                    {confirmWarning.ladders.map(ladder => (
                                        <li key={ladder.id} className={`${teamStyles.ladderItem} ${commonStyles.warningText}`}>
                                            {ladder.name}
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}
                        <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
                            <button
                                type="button"
                                className={`${btnStyles.linkButton} ${formStyles.btnSecondary}`}
                                onClick={() => setConfirmWarning(null)}
                            >
                                {/* Cancel keeps the warning state but returns the user to the search results. */}
                                {texts.cancel_btn || "Cancel"}
                            </button>
                            <button
                                type="button"
                                className={`${btnStyles.primaryButton} ${formStyles.btnSecondary}`}
                                onClick={handleCreateNewTeam}
                            >
                                {texts.create_new_team || "Create new team"}
                            </button>
                            <button
                                type="button"
                                className={`${btnStyles.nextBtn} ${formStyles.btnSecondary}`}
                                onClick={handleConfirmExceed}
                                disabled={addingId}
                            >
                                {addingId ? <Spinner /> : (texts.add_player_confirm_exceed || "Remove from ladders and add")}
                            </button>
                        </div>
                    </div>
                </FormPage>
            )}

            {/* --- Page 0: search and results ------------------------- */}
            {!confirmWarning && (
                <FormPage active={true}>

                    {/* Search input */}
                    <div className={teamStyles.searchRow}>
                        {/* The search field drives the player lookup hook and keeps the results live while typing. */}
                        <input
                            ref={inputRef}
                            className={formStyles.formInput}
                            type="text"
                            placeholder={texts.add_player_search_placeholder || "Name, email, or ID..."}
                            value={query}
                            onChange={e => setQuery(e.target.value)}
                        />
                        {searching && (
                            <span className={teamStyles.searchSpinner}>
                                <Spinner />
                            </span>
                        )}
                    </div>

                    {/* Hint if nothing is entered */}
                    {!query.trim() && (
                        <p className={`${commonStyles.muted} ${teamStyles.noResults}`}>
                            {texts.add_player_search_hint || "Type to search accounts."}
                        </p>
                    )}

                    {/* Empty result */}
                    {!searching && !searchErr && query.trim() && results.length === 0 && (
                        <p className={`${commonStyles.muted} ${teamStyles.noResults}`}>
                            {texts.add_player_no_results || "No accounts found."}
                        </p>
                    )}

                    {/* Search results */}
                    {results.length > 0 && (
                        <ul className={`${panelStyles.list} ${teamStyles.resultsList}`}>
                            {results.map(account => (
                                <SearchResultCard
                                    key={account.id}
                                    account={account}
                                    isAdding={addingId === account.id}
                                    isAdded={addedIds.has(account.id)}
                                    onAdd={() => addPlayer(account.id)}
                                    texts={texts}
                                />
                            ))}
                        </ul>
                    )}

                </FormPage>
            )}
        </FormPanel>
    );
}

/* -- Search result card ------------------------------------------------------- */

function SearchResultCard({ account, isAdding, isAdded, onAdd, texts = {} }) {
    const fullName = [account.firstName, account.lastName].filter(Boolean).join(" ") || "-";

    return (
        <ItemCard>
            <div className={teamStyles.resultInfo}>
                {/* Name and email are shown together so staff can confirm they picked the right person. */}
                <p className={commonStyles.primaryText}>{fullName}</p>
                <p className={commonStyles.secondaryText}>{account.email}</p>
            </div>
            <button
                className={`${teamStyles.addBtn} ${isAdded ? teamStyles.addBtnDone : ""}`}
                onClick={onAdd}
                disabled={isAdding || isAdded}
                aria-label={isAdded ? (texts.added_label || "Added") : `${texts.add_player_btn || "Add"} ${fullName}`}
            >
                {/* This button is the direct add action for one search result.
                    It is disabled while the request is in flight or already done. */}
                {isAdding ? <Spinner /> : isAdded ? "+" : <PlusIcon />}
            </button>
        </ItemCard>
    );
}
