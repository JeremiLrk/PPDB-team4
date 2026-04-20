import { useState, useEffect } from "react";
import styles from "@/style/ClubSettings.module.css";

export function ClubLadders({ ladders = [], onCreate }) {
    const [form, setForm] = useState({
        name: "",
        description: "",
        ruleset_id: "" // Added field
    });

    const [rulesets, setRulesets] = useState([]);
    const [submitting, setSubmitting] = useState(false);

    // Fetch rulesets for the dropdown
    useEffect(() => {
        fetch('/api/rulesets')
            .then(res => res.ok ? res.json() : [])
            .then(data => setRulesets(data))
            .catch(err => console.error(err));
    }, []);

    const handleChange = (e) => {
        setForm(prev => ({
            ...prev,
            [e.target.name]: e.target.value
        }));
    };

    const handleCreate = async () => {
        if (!form.name.trim()) return;

        setSubmitting(true);
        await onCreate({
            ...form,
            // Convert to integer if selected, otherwise pass null
            ruleset_id: form.ruleset_id ? parseInt(form.ruleset_id) : null,
            ladder_rating_function_id: 1
        });

        setForm({ name: "", description: "", ruleset_id: "" });
        setSubmitting(false);
    };

    return (
        <div className={`${styles.contentGrid} ${styles.contentFade}`}>
            {/* Create */}
            <article className={styles.panel}>
                <h3 className={styles.panelTitle}>Create Ladder</h3>

                <div className={styles.form}>
                    <input
                        className={styles.formInput}
                        name="name"
                        placeholder="Ladder name"
                        value={form.name}
                        onChange={handleChange}
                    />

                    <textarea
                        className={styles.formTextarea}
                        name="description"
                        placeholder="Description"
                        value={form.description}
                        onChange={handleChange}
                        rows={3}
                    />

                    {/* NEW: Ruleset Dropdown */}
                    <select
                        className={styles.formInput}
                        name="ruleset_id"
                        value={form.ruleset_id}
                        onChange={handleChange}
                        style={{ appearance: 'auto' }} // Ensures default dropdown arrow shows
                    >
                        <option value="">No Ruleset (Default)</option>
                        {rulesets.map(rs => (
                            <option key={rs.id} value={rs.id}>
                                {rs.name}
                            </option>
                        ))}
                    </select>

                    <button
                        className={styles.submitButton}
                        onClick={handleCreate}
                        disabled={submitting}
                    >
                        {submitting ? "Creating..." : "Create Ladder"}
                    </button>
                </div>
            </article>

            {/* List */}
            <article className={styles.panel}>
                <h3 className={styles.panelTitle}>Ladders</h3>

                {ladders.length === 0 ? (
                    <p className={styles.muted}>No ladders yet.</p>
                ) : (
                    <ul className={styles.list}>
                        {ladders.map(l => (
                            <li key={l.id} className={styles.listItem}>
                                <div>
                                    <p className={styles.primaryText}>{l.name}</p>
                                    <p className={styles.secondaryText}>
                                        {l.description || "No description"}
                                    </p>
                                    {/* Optional: Show attached ruleset ID if you want */}
                                    {l.ruleset_id && (
                                        <p className={styles.secondaryText} style={{fontSize: '0.75rem', color: '#14b8a6'}}>
                                            Ruleset ID: {l.ruleset_id}
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