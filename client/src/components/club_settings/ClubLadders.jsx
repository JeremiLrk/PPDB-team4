import { useState } from "react";
import { useSportTypes } from "@/hooks/useSportTypes"; 
import styles from "@/style/ClubSettings.module.css";

export function ClubLadders({ ladders = [], onCreate, ratingFunctions = [], ruleSets = [] }) {
    const { sportTypes } = useSportTypes();

    const [form, setForm] = useState({
        name: "",
        description: "",
        sport_type_id: "",
        rule_set_id: "", // Now using these
        ladder_rating_function_id: "" // Now using these
    });

    const [submitting, setSubmitting] = useState(false);

    const handleChange = (e) => {
        setForm(prev => ({
            ...prev,
            [e.target.name]: e.target.value
        }));
    };

    const handleCreate = async () => {
        // Basic validation
        if (!form.name.trim() || !form.sport_type_id || !form.rule_set_id || !form.ladder_rating_function_id) {
            alert("Please fill in all required fields");
            return;
        }

        setSubmitting(true);
        
        // We send the IDs (converted to Numbers) to the backend
        await onCreate({
            ...form,
            sport_type_id: Number(form.sport_type_id),
            ruleset_id: Number(form.rule_set_id),
            ladder_rating_function_id: Number(form.ladder_rating_function_id)
        });

        // Reset form
        setForm({ name: "", description: "", sport_type_id: "", rule_set_id: "", ladder_rating_function_id: "" });
        setSubmitting(false);
    };

    return (
        <div className={`${styles.contentGrid} ${styles.contentFade}`}>
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

                    {/* Sport Type Dropdown */}
                    <select className={styles.formInput} name="sport_type_id" value={form.sport_type_id} onChange={handleChange}>
                        <option value="" disabled>Select Sport Type</option>
                        {sportTypes.map(s => (
                            <option key={s.id} value={s.id}>{s.name}</option>
                        ))}
                    </select>

                    {/* Rule Set Dropdown - User sees Name, Form gets ID */}
                    <select className={styles.formInput} name="rule_set_id" value={form.rule_set_id} onChange={handleChange}>
                        <option value="" disabled>Select Rule Set</option>
                        {ruleSets.map(r => (
                            <option key={r.id} value={r.id}>{r.name}</option>
                        ))}
                    </select>

                    {/* Rating Function Dropdown - User sees Name, Form gets ID */}
                    <select className={styles.formInput} name="ladder_rating_function_id" value={form.ladder_rating_function_id} onChange={handleChange}>
                        <option value="" disabled>Select Rating System</option>
                        {ratingFunctions.map(rf => (
                            <option key={rf.id} value={rf.id}>{rf.name}</option>
                        ))}
                    </select>

                    <textarea
                        className={styles.formTextarea}
                        name="description"
                        placeholder="Description"
                        value={form.description}
                        onChange={handleChange}
                        rows={3}
                    />

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
