// Club settings UI component for ClubOwners.

import { useState } from "react";
import styles from "@/style/ClubSettings.module.css";

function defaultText(lang, english, dutch) {
    /*
     Returns a language-aware fallback label.
    */
    return String(lang || "").toLowerCase().startsWith("nl") ? dutch : english;
}

export function Clubowners({ owners, onRemove, onAdd, searchAccounts, texts = {}, lang = "en" }) {
    /*
     Owns the owner search/add flow and the current owner list.
    */
    const [query, setQuery] = useState("");
    const [results, setResults] = useState([]);
    const [isSearching, setIsSearching] = useState(false);
    const handleSearch = async (e) => {
        /*
         Searches for users once the typed query is long enough.
        */
        const value = e.target.value;
        setQuery(value);

        if (value.length > 2) {
            // Wait for a short query before hitting the search endpoint.
            setIsSearching(true);
            const accounts = await searchAccounts(value);
            setResults(accounts);
            setIsSearching(false);
        } else {
            // Short queries are cleared so we do not spam the backend.
            setResults([]);
        }
    };

    const handleAdd = (userId) => {
        /*
         Adds one owner and clears the search results.
        */
        onAdd(userId);
        setQuery("");
        setResults([]);
    };

    return (
        <div className={styles.contentGrid}>
            {/* Search & Add Panel */}
            <article className={`${styles.panel} ${styles.contentFade}`}>
                <h3 className={styles.panelTitle}>{texts.owners_add_title || defaultText(lang, "Add new owner", "Nieuwe eigenaar toevoegen")}</h3>
                <div className={styles.form} style={{ marginTop: '1rem' }}>
                    <input
                        type="text"
                        className={styles.formInput}
                        placeholder={texts.owners_search_placeholder || defaultText(lang, "Search by name or email...", "Zoek op naam of e-mail...")}
                        value={query}
                        onChange={handleSearch}
                    />
                    
                    {/* Search Results Dropdown */}
                    {results.length > 0 && (
                        <ul className={styles.list} style={{ marginTop: '0.5rem', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}>
                            {results.map(user => (
                                <li key={user.id} className={styles.listItem}>
                                    <div style={{ display: 'flex', flexDirection: 'column' }}>
                                        {/* Full Name is prominent */}
                                        <p className={styles.primaryText} style={{ fontWeight: '600' }}>
                                            {user.name}
                                        </p>
                                        {/* Email is clearly visible beneath */}
                                        <p className={styles.secondaryText} style={{ fontSize: '0.8rem', opacity: 0.7 }}>
                                            {user.email}
                                        </p>
                                    </div>
                                    <button 
                                        className={styles.linkButton} 
                                        onClick={() => handleAdd(user.id)}
                                        style={{ color: '#4ade80', marginLeft: 'auto' }}
                                    >
                                        {/* Adding an owner is just selecting one of the searched accounts. */}
                                        {texts.add || defaultText(lang, "Add", "Toevoegen")} +
                                    </button>
                                </li>
                            ))}
                        </ul>
                    )}
                    {query.length > 2 && results.length === 0 && !isSearching && (
                            <p className={styles.muted} style={{ padding: '0.5rem' }}>{texts.owners_no_users || defaultText(lang, "No users found.", "Geen gebruikers gevonden.")}</p>
                        )}
                </div>
            </article>

            {/* Existing Owners List Panel */}
            <article className={`${styles.panel} ${styles.contentFade}`}>
                <div className={styles.panelTopRow}>
                    <h3 className={styles.panelTitle}>{texts.owners_title || defaultText(lang, "Current owners", "Huidige eigenaren")}</h3>
                    <span className={styles.counter}>{owners.length}</span>
                </div>

                {owners.length === 0 ? (
                    <p className={styles.muted}>{texts.owners_no_owners || defaultText(lang, "No owners yet.", "Nog geen eigenaren.")}</p>
                ) : (
                    <ul className={styles.list}>
                        {owners.map(m => (
                            <li key={m.id} className={styles.listItem}>
                                <div>
                                    <p className={styles.primaryText}>{m.email}</p>
                                    <p className={styles.secondaryText}>{m.name || texts.owner_label || defaultText(lang, "Owner", "Eigenaar")}</p>
                                </div>

                                <button
                                    onClick={() => onRemove(m.id)}
                                    className={styles.linkButton}
                                    style={{ color: '#f87171' }}
                                >
                                    {texts.remove || defaultText(lang, "Remove", "Verwijderen")}
                                </button>
                            </li>
                        ))}
                    </ul>
                )}
            </article>
        </div>
    );
}

export default Clubowners;
