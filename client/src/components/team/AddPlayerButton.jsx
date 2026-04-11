import commonStyles from "@/style/common/Common.module.css";
import formStyles   from "@/style/common/Forms.module.css";
import panelStyles  from "@/style/common/Panel.module.css";
import teamStyles   from "@/style/TeamSettings.module.css";

import { useAddPlayer } from "@/hooks/teams/useAddPlayer.js";
import { PlusIcon }     from "@/components/icon/PlusIcon.jsx";
import { Spinner }      from "@/components/forms/Spinner.jsx";
import { FormPanel }    from "@/components/forms/FormPanel.jsx";
import { FormPage }     from "@/components/forms/FormPage.jsx";
import ItemCard         from "@/components/common/ItemCard.jsx";
import { useRef } from "react";

/**
 * AddPlayerButton - dropdown panel for searching and adding players to a team.
 *
 * Props:
 *   teamId    {number|string}  - the team to add players to
 *   onAdded   {() => void}     - called after a player is successfully added
 */
export default function AddPlayerButton({ teamId, onAdded }) {
    const {
        isOpen, openPanel, closePanel,
        query, setQuery,
        results, searching, searchErr,
        addPlayer, addingId, addedIds, addErr,
        inputRef, // авто-фокус керується хуком
    } = useAddPlayer({ teamId, onAdded });

    return (
        <FormPanel
            title="Add Player"
            triggerContent={<><PlusIcon rotated={isOpen} /> Add Player</>}

            isOpen={isOpen}
            openPanel={openPanel}
            closePanel={closePanel}

            // One page - navigation hidden automatically
            step={0}
            totalSteps={1}
            onNext={null}
            onBack={null}
            onSubmit={null}

            // No loading/success state at the panel level —
            // each result card has its own state
            isLoading={false}
            isSuccess={false}

            error={addErr || searchErr || null}

            panelClassName={teamStyles.addPlayerPanel}
            ariaLabel="Add player to team"

        >
            {/* --- Page 0: search and results ------------------------- */}
            <FormPage active={true}>

                {/* Search input */}
                <div className={teamStyles.searchRow}>
                    <input
                        ref={inputRef}
                        className={formStyles.formInput}
                        type="text"
                        placeholder="Name, email, or ID…"
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
                        Type to search accounts.
                    </p>
                )}

                {/* Empty result */}
                {!searching && !searchErr && query.trim() && results.length === 0 && (
                    <p className={`${commonStyles.muted} ${teamStyles.noResults}`}>
                        No accounts found.
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
                            />
                        ))}
                    </ul>
                )}

            </FormPage>
        </FormPanel>
    );
}

/* -- Search result card ------------------------------------------------------- */

function SearchResultCard({ account, isAdding, isAdded, onAdd }) {
    const fullName = [account.firstName, account.lastName].filter(Boolean).join(" ") || "-";

    return (
        <ItemCard>
            <div className={teamStyles.resultInfo}>
                <p className={commonStyles.primaryText}>{fullName}</p>
                <p className={commonStyles.secondaryText}>{account.email}</p>
            </div>
            <button
                className={`${teamStyles.addBtn} ${isAdded ? teamStyles.addBtnDone : ""}`}
                onClick={onAdd}
                disabled={isAdding || isAdded}
                aria-label={isAdded ? "Added" : `Add ${fullName}`}
            >
                {isAdding ? <Spinner /> : isAdded ? "✓" : <PlusIcon />}
            </button>
        </ItemCard>
    );
}