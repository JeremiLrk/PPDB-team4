import { useState } from "react";
import styles from "@/style/ClubSettings.module.css";

export function ClubLadders({ ladders = [], onCreate }) {
    const [form, setForm] = useState({
        name: "",
        description: "",
    });

    const [submitting, setSubmitting] = useState(false);

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
            ladder_rating_function_id: 1
        });

        setForm({ name: "", description: "" });
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