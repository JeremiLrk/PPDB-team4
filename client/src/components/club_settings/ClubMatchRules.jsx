import { useState, useEffect } from "react";
import styles from "@/style/ClubSettings.module.css";

export default function ClubMatchRules() {
    const [rules, setRules] = useState([]);
    const [rulesets, setRulesets] = useState([]);

    // Forms state
    const [newRuleContent, setNewRuleContent] = useState("");
    const [newRulesetName, setNewRulesetName] = useState("");
    const [selectedRuleIds, setSelectedRuleIds] = useState([]);
    const [submitting, setSubmitting] = useState(false);

    // Fetch data on load
    useEffect(() => {
        fetchRules();
        fetchRulesets();
    }, []);

    const fetchRules = async () => {
        try {
            const res = await fetch('/api/rules');
            if (res.ok) setRules(await res.json());
        } catch (err) { console.error(err); }
    };

    const fetchRulesets = async () => {
        try {
            const res = await fetch('/api/rulesets');
            if (res.ok) setRulesets(await res.json());
        } catch (err) { console.error(err); }
    };

    const handleCreateRule = async () => {
        if (!newRuleContent.trim()) return;
        setSubmitting(true);
        try {
            const res = await fetch('/api/rules', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content: newRuleContent })
            });
            if (res.ok) {
                setNewRuleContent("");
                fetchRules(); // Refresh list
            }
        } finally {
            setSubmitting(false);
        }
    };

    const handleCreateRuleset = async () => {
        if (!newRulesetName.trim()) return;
        setSubmitting(true);
        try {
            const res = await fetch('/api/rulesets', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: newRulesetName,
                    rule_ids: selectedRuleIds
                })
            });
            if (res.ok) {
                setNewRulesetName("");
                setSelectedRuleIds([]);
                fetchRulesets(); // Refresh list
            }
        } finally {
            setSubmitting(false);
        }
    };

    const toggleRuleSelection = (id) => {
        setSelectedRuleIds(prev =>
            prev.includes(id) ? prev.filter(r => r !== id) : [...prev, id]
        );
    };

    return (
        <div className={`${styles.contentGrid} ${styles.contentFade}`}>
            {/* Panel 1: Rule Library */}
            <article className={styles.panel}>
                <h3 className={styles.panelTitle}>Rule Library</h3>

                <div className={styles.form}>
                    <input
                        className={styles.formInput}
                        placeholder="E.g., Match must be won by 2 points"
                        value={newRuleContent}
                        onChange={(e) => setNewRuleContent(e.target.value)}
                    />
                    <button
                        className={styles.submitButton}
                        onClick={handleCreateRule} disabled={submitting}
                    >
                        Add Single Rule
                    </button>
                </div>

                <div className="mt-6">
                    <h4 className={styles.secondaryText}>Available Rules:</h4>
                    <ul className={styles.list} style={{marginTop: '10px'}}>
                        {rules.map(r => (
                            <li key={r.id} className={styles.listItem} style={{padding: '8px'}}>
                                <p className={styles.primaryText} style={{fontSize: '0.9rem'}}>{r.content}</p>
                            </li>
                        ))}
                    </ul>
                </div>
            </article>

            {/* Panel 2: Ruleset Builder */}
            <article className={styles.panel}>
                <h3 className={styles.panelTitle}>Build Ruleset</h3>

                <div className={styles.form}>
                    <input
                        className={styles.formInput}
                        placeholder="Ruleset Name (e.g., Pro Tournament)"
                        value={newRulesetName}
                        onChange={(e) => setNewRulesetName(e.target.value)}
                    />

                    <div className="my-4" style={{maxHeight: '200px', overflowY: 'auto'}}>
                        <p className={styles.secondaryText} style={{marginBottom: '8px'}}>Select Rules to Include:</p>
                        {rules.map(r => (
                            <label key={r.id} style={{display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px', cursor: 'pointer'}}>
                                <input
                                    type="checkbox"
                                    checked={selectedRuleIds.includes(r.id)}
                                    onChange={() => toggleRuleSelection(r.id)}
                                />
                                <span className={styles.primaryText} style={{fontSize: '0.85rem'}}>{r.content}</span>
                            </label>
                        ))}
                    </div>

                    <button
                        className={styles.submitButton}
                        onClick={handleCreateRuleset} disabled={submitting}
                    >
                        Save Ruleset
                    </button>
                </div>

                <div className="mt-6">
                    <h4 className={styles.secondaryText}>Existing Rulesets:</h4>
                    <ul className={styles.list} style={{marginTop: '10px'}}>
                        {rulesets.map(rs => (
                            <li key={rs.id} className={styles.listItem} style={{padding: '8px', flexDirection: 'column', alignItems: 'flex-start'}}>
                                <p className={styles.primaryText}>{rs.name}</p>
                                <p className={styles.secondaryText} style={{fontSize: '0.75rem'}}>
                                    Contains {rs.rules?.length || 0} rules
                                </p>
                            </li>
                        ))}
                    </ul>
                </div>
            </article>
        </div>
    );
}