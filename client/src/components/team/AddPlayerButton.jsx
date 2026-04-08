import { useRef, useEffect } from "react";
import styles      from "@/style/common/Forms.module.css";
import teamStyles  from "@/style/TeamSettings.module.css";
import commonStyles from "@/style/common/Common.module.css";
import { useAddPlayer }  from "@/hooks/teams/useAddPlayer.js";
import { PlusIcon }      from "@/components/icon/PlusIcon.jsx";
import { Spinner }       from "@/components/forms/Spinner.jsx";
import ItemCard          from "@/components/common/ItemCard.jsx";

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
    } = useAddPlayer({ teamId, onAdded });

    const panelRef   = useRef(null);
    const triggerRef = useRef(null);
    const inputRef   = useRef(null);

    // Close on outside click
    useEffect(() => {
        if (!isOpen) return;
        function onOutside(e) {
            if (
                panelRef.current   && !panelRef.current.contains(e.target) &&
                triggerRef.current && !triggerRef.current.contains(e.target)
            ) closePanel();
        }
        document.addEventListener("mousedown", onOutside);
        return () => document.removeEventListener("mousedown", onOutside);
    }, [isOpen, closePanel]);

    // Close on Escape
    useEffect(() => {
        if (!isOpen) return;
        function onKey(e) { if (e.key === "Escape") closePanel(); }
        document.addEventListener("keydown", onKey);
        return () => document.removeEventListener("keydown", onKey);
    }, [isOpen, closePanel]);

    // Auto-focus input when panel opens
    useEffect(() => {
        if (isOpen) setTimeout(() => inputRef.current?.focus(), 60);
    }, [isOpen]);

    return (
        <div className={styles.wrapper}>
            {/* Trigger */}
            <button
                ref={triggerRef}
                onClick={isOpen ? closePanel : openPanel}
                className={`${styles.trigger} ${isOpen ? styles.triggerOpen : ""}`}
                aria-expanded={isOpen}
                aria-haspopup="dialog"
            >
                <PlusIcon rotated={isOpen} />
                Add Player
            </button>

            {/* Panel */}
            <div
                ref={panelRef}
                role="dialog"
                aria-label="Add player to team"
                aria-modal="true"
                className={`${styles.panel} ${teamStyles.addPlayerPanel} ${isOpen ? styles.panelOpen : ""}`}
            >
                {/* Header */}
                <div className={styles.panelHeader}>
                    <p className={styles.panelTitle}>Add Player</p>
                    <button
                        className={styles.closeBtn}
                        onClick={closePanel}
                        aria-label="Close"
                    >
                        ×
                    </button>
                </div>

                {/* Body */}
                <div className={styles.panelBody}>
                    {/* Search input */}
                    <div className={teamStyles.searchRow}>
                        <input
                            ref={inputRef}
                            className={styles.formInput}
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

                    {/* Add error */}
                    {addErr && <p className={styles.error}>{addErr}</p>}

                    {/* Search error */}
                    {searchErr && <p className={styles.error}>{searchErr}</p>}

                    {/* Empty state */}
                    {!searching && !searchErr && query.trim() && results.length === 0 && (
                        <p className={`${commonStyles.muted} ${teamStyles.noResults}`}>
                            No accounts found.
                        </p>
                    )}

                    {/* Hint when no query */}
                    {!query.trim() && (
                        <p className={`${commonStyles.muted} ${teamStyles.noResults}`}>
                            Type to search accounts.
                        </p>
                    )}

                    {/* Results */}
                    {results.length > 0 && (
                        <ul className={`${commonStyles.list} ${teamStyles.resultsList}`}>
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
                </div>
            </div>
        </div>
    );
}

/* ── Search result card ── */

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
                {isAdding ? (
                    <Spinner />
                ) : isAdded ? (
                    "✓"
                ) : (
                    <PlusIcon />
                )}
            </button>
        </ItemCard>
    );
}
