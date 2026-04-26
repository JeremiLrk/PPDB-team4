import { useState } from "react";
import styles from "@/style/ClubSettings.module.css";

export function Clubowners({ owners, onRemove, onAdd, searchAccounts, texts = {} }) {
    const [query, setQuery] = useState("");
    const [results, setResults] = useState([]);
    const [isSearching, setIsSearching] = useState(false);

    const handleSearch = async (e) => {
        const value = e.target.value;
        setQuery(value);

        if (value.length > 2) {
            setIsSearching(true);
            const accounts = await searchAccounts(value);
            setResults(accounts);
            setIsSearching(false);
        } else {
            setResults([]);
        }
    };

    const handleAdd = (userId) => {
        onAdd(userId);
        setQuery(""); // Clear search after adding
        setResults([]);
    };

    return (
        <div className={styles.contentGrid}>
            {/* Search & Add Panel */}
            <article className={`${styles.panel} ${styles.contentFade}`}>
                <h3 className={styles.panelTitle}>{texts.owners_add_title || "Nieuwe eigenaar toevoegen"}</h3>
                <div className={styles.form} style={{ marginTop: '1rem' }}>
                    <input
                        type="text"
                        className={styles.formInput}
                        placeholder={texts.owners_search_placeholder || "Zoek op naam of e-mail..."}
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
                                        Toevoegen +
                                    </button>
                                </li>
                            ))}
                        </ul>
                    )}
                    {query.length > 2 && results.length === 0 && !isSearching && (
                            <p className={styles.muted} style={{ padding: '0.5rem' }}>{texts.owners_no_users || "Geen gebruikers gevonden."}</p>
                        )}
                </div>
            </article>

            {/* Existing Owners List Panel */}
            <article className={`${styles.panel} ${styles.contentFade}`}>
                <div className={styles.panelTopRow}>
                    <h3 className={styles.panelTitle}>{texts.owners_title || "Huidige eigenaren"}</h3>
                    <span className={styles.counter}>{owners.length}</span>
                </div>

                {owners.length === 0 ? (
                    <p className={styles.muted}>{texts.owners_no_owners || "Nog geen eigenaren."}</p>
                ) : (
                    <ul className={styles.list}>
                        {owners.map(m => (
                            <li key={m.id} className={styles.listItem}>
                                <div>
                                    <p className={styles.primaryText}>{m.email}</p>
                                    <p className={styles.secondaryText}>{m.name || texts.owner_label || "Eigenaar"}</p>
                                </div>

                                <button
                                    onClick={() => onRemove(m.id)}
                                    className={styles.linkButton}
                                    style={{ color: '#f87171' }}
                                >
                                    {texts.remove || "Verwijderen"}
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
