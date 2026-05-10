import { useCallback, useEffect, useState } from "react";
import styles from "@/style/ClubSettings.module.css";

const MATCH_FORMAT_OPTIONS = [
    { value: "best_of_3", label: "Best of 3 sets" },
    { value: "timed",     label: "Op tijd spelen" },
    { value: "pro_set",   label: "Pro Set (één lange set)" },
];

const THIRD_SET_OPTIONS = [
    { value: "super_tiebreak", label: "Super Tiebreak (tot 10 punten)" },
    { value: "full_set",       label: "Volledige derde set" },
];

const DEUCE_OPTIONS = [
    { value: "advantage",    label: "Klassiek (Voordeel)" },
    { value: "golden_point", label: "Golden Point (No-Ad)" },
];

const GAME_FORMAT_OPTIONS = [
    { value: "doubles", label: "Dubbelspel (2v2)" },
    { value: "singles", label: "Enkelspel (1v1)" },
];

const EMPTY_FORM = {
    name:                 "",
    description:          "",
    matchFormat:          "best_of_3",
    timedDurationMinutes: 60,
    proSetGames:          8,
    thirdSetFormat:       "super_tiebreak",
    deuceRule:            "advantage",
    gameFormat:           "doubles",
    canBeUsedByOthers:    true,
};

function formatRuleSetSummary(rs) {
    const parts = [];

    const formatLabel = MATCH_FORMAT_OPTIONS.find(o => o.value === rs.matchFormat)?.label ?? rs.matchFormat;
    if (rs.matchFormat === "timed") {
        parts.push(`${formatLabel} – ${rs.timedDurationMinutes} min`);
    } else if (rs.matchFormat === "pro_set") {
        parts.push(`${formatLabel} tot ${rs.proSetGames} games`);
    } else {
        parts.push(formatLabel);
    }

    if (rs.matchFormat === "best_of_3") {
        parts.push(THIRD_SET_OPTIONS.find(o => o.value === rs.thirdSetFormat)?.label ?? rs.thirdSetFormat);
    }

    parts.push(DEUCE_OPTIONS.find(o => o.value === rs.deuceRule)?.label ?? rs.deuceRule);
    parts.push(GAME_FORMAT_OPTIONS.find(o => o.value === rs.gameFormat)?.label ?? rs.gameFormat);

    return parts.join(" · ");
}

export default function ClubMatchRules({ clubId, texts = {} }) {
    const [ruleSets, setRuleSets] = useState([]);
    const [loading, setLoading]   = useState(true);
    const [error, setError]       = useState("");
    const [submitting, setSubmitting] = useState(false);
    const [form, setForm] = useState(EMPTY_FORM);

    const fetchData = useCallback(async () => {
        setLoading(true);
        setError("");
        try {
            const res  = await fetch("/api/match-rule-sets?from=0&to=200", { credentials: "include" });
            const data = await res.json().catch(() => ({}));
            if (!res.ok) throw new Error(data?.message || "Regelsets konden niet worden geladen.");
            setRuleSets(Array.isArray(data.ruleSets) ? data.ruleSets : []);
        } catch (err) {
            setError(err?.message || "Regelsets konden niet worden geladen.");
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { void fetchData(); }, [fetchData]);

    function updateForm(field, value) {
        setForm(prev => ({ ...prev, [field]: value }));
    }

    async function handleCreate() {
        const name = form.name.trim();
        if (!name) return;

        setSubmitting(true);
        setError("");
        try {
            const body = {
                name,
                description:          form.description.trim() || undefined,
                matchFormat:          form.matchFormat,
                thirdSetFormat:       form.thirdSetFormat,
                deuceRule:            form.deuceRule,
                gameFormat:           form.gameFormat,
                canBeUsedByOthers:    form.canBeUsedByOthers,
                clubId:               clubId ? Number(clubId) : null,
            };
            if (form.matchFormat === "timed")   body.timedDurationMinutes = Number(form.timedDurationMinutes);
            if (form.matchFormat === "pro_set")  body.proSetGames          = Number(form.proSetGames);

            const res  = await fetch("/api/match-rule-sets", {
                method:  "POST",
                credentials: "include",
                headers: { "Content-Type": "application/json" },
                body:    JSON.stringify(body),
            });
            const data = await res.json().catch(() => ({}));
            if (!res.ok) throw new Error(data?.message || "Regelset kon niet worden aangemaakt.");
            setForm(EMPTY_FORM);
            await fetchData();
        } catch (err) {
            setError(err?.message || "Regelset kon niet worden aangemaakt.");
        } finally {
            setSubmitting(false);
        }
    }

    async function handleDelete(id) {
        if (!window.confirm("Regelset verwijderen?")) return;
        setError("");
        try {
            const res = await fetch(`/api/match-rule-sets/${id}`, {
                method: "DELETE",
                credentials: "include",
            });
            if (!res.ok) {
                const data = await res.json().catch(() => ({}));
                throw new Error(data?.message || "Verwijderen mislukt.");
            }
            await fetchData();
        } catch (err) {
            setError(err?.message || "Verwijderen mislukt.");
        }
    }

    if (loading) {
        return (
            <div className={`${styles.contentGrid} ${styles.contentFade}`}>
                <article className={styles.panel}>
                    <h3 className={styles.panelTitle}>Wedstrijdregels</h3>
                    <p className={styles.muted}>Regelsets laden...</p>
                </article>
            </div>
        );
    }

    return (
        <div className={`${styles.contentGrid} ${styles.contentFade}`}>

            {/* Create form */}
            <article className={styles.panel}>
                <h3 className={styles.panelTitle}>{texts.create_rule_set_title || "Nieuwe regelset"}</h3>

                <div className={styles.form}>
                    <input
                        className={styles.formInput}
                        placeholder={texts.rule_set_name_placeholder || "Naam van de regelset"}
                        value={form.name}
                        onChange={e => updateForm("name", e.target.value)}
                    />
                    <textarea
                        className={styles.formTextarea}
                        placeholder={texts.rule_description_placeholder || "Omschrijving (optioneel)"}
                        value={form.description}
                        onChange={e => updateForm("description", e.target.value)}
                        rows={2}
                    />

                    {/* Match format */}
                    <label className={styles.secondaryText}>
                        {texts.match_format_label || "Wedstrijdformaat"}
                    </label>
                    <select
                        className={styles.formInput}
                        value={form.matchFormat}
                        onChange={e => updateForm("matchFormat", e.target.value)}
                    >
                        {MATCH_FORMAT_OPTIONS.map(o => (
                            <option key={o.value} value={o.value}>{o.label}</option>
                        ))}
                    </select>

                    {form.matchFormat === "timed" && (
                        <input
                            className={styles.formInput}
                            type="number"
                            min={10}
                            max={300}
                            placeholder={texts.timed_duration_placeholder || "Speelduur in minuten (bijv. 60)"}
                            value={form.timedDurationMinutes}
                            onChange={e => updateForm("timedDurationMinutes", e.target.value)}
                        />
                    )}

                    {form.matchFormat === "pro_set" && (
                        <input
                            className={styles.formInput}
                            type="number"
                            min={4}
                            max={20}
                            placeholder={texts.pro_set_games_placeholder || "Aantal games voor Pro Set (bijv. 8)"}
                            value={form.proSetGames}
                            onChange={e => updateForm("proSetGames", e.target.value)}
                        />
                    )}

                    {/* Third set – only relevant for best_of_3 */}
                    {form.matchFormat === "best_of_3" && (
                        <>
                            <label className={styles.secondaryText}>
                                {texts.third_set_label || "Derde set bij 1-1 stand"}
                            </label>
                            <select
                                className={styles.formInput}
                                value={form.thirdSetFormat}
                                onChange={e => updateForm("thirdSetFormat", e.target.value)}
                            >
                                {THIRD_SET_OPTIONS.map(o => (
                                    <option key={o.value} value={o.value}>{o.label}</option>
                                ))}
                            </select>
                        </>
                    )}

                    {/* Deuce rule */}
                    <label className={styles.secondaryText}>
                        {texts.deuce_rule_label || "40-40 regel (Deuce)"}
                    </label>
                    <select
                        className={styles.formInput}
                        value={form.deuceRule}
                        onChange={e => updateForm("deuceRule", e.target.value)}
                    >
                        {DEUCE_OPTIONS.map(o => (
                            <option key={o.value} value={o.value}>{o.label}</option>
                        ))}
                    </select>

                    {/* Game format */}
                    <label className={styles.secondaryText}>
                        {texts.game_format_label || "Spelvorm"}
                    </label>
                    <select
                        className={styles.formInput}
                        value={form.gameFormat}
                        onChange={e => updateForm("gameFormat", e.target.value)}
                    >
                        {GAME_FORMAT_OPTIONS.map(o => (
                            <option key={o.value} value={o.value}>{o.label}</option>
                        ))}
                    </select>

                    <label className={styles.secondaryText} style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
                        <input
                            type="checkbox"
                            checked={form.canBeUsedByOthers}
                            onChange={e => updateForm("canBeUsedByOthers", e.target.checked)}
                        />
                        {texts.use_by_others || "Door anderen te gebruiken"}
                    </label>

                    <button
                        className={styles.submitButton}
                        onClick={handleCreate}
                        disabled={submitting || !form.name.trim()}
                        type="button"
                    >
                        {submitting
                            ? (texts.saving_rule_set || "Bezig met opslaan...")
                            : (texts.save_rule_set  || "Regelset opslaan")}
                    </button>
                </div>
            </article>

            {/* List */}
            <article className={styles.panel}>
                <h3 className={styles.panelTitle}>{texts.existing_rule_sets || "Bestaande regelsets"}</h3>

                {ruleSets.length === 0 ? (
                    <p className={styles.muted}>{texts.no_rule_sets || "Nog geen regelsets."}</p>
                ) : (
                    <ul className={styles.list} style={{ marginTop: "10px" }}>
                        {ruleSets.map(rs => (
                            <li
                                key={rs.id}
                                className={styles.listItem}
                                style={{ padding: "10px", flexDirection: "column", alignItems: "flex-start", gap: "4px" }}
                            >
                                <div style={{ display: "flex", justifyContent: "space-between", width: "100%", alignItems: "center" }}>
                                    <p className={styles.primaryText} style={{ fontWeight: 600 }}>{rs.name}</p>
                                    {rs.creatorId && (
                                        <button
                                            className={styles.dangerButton ?? styles.submitButton}
                                            style={{ fontSize: "0.75rem", padding: "2px 8px" }}
                                            onClick={() => handleDelete(rs.id)}
                                            type="button"
                                        >
                                            {texts.delete || "Verwijder"}
                                        </button>
                                    )}
                                </div>
                                <p className={styles.secondaryText} style={{ fontSize: "0.8rem" }}>
                                    {formatRuleSetSummary(rs)}
                                </p>
                                {rs.description && (
                                    <p className={styles.secondaryText} style={{ fontSize: "0.75rem", fontStyle: "italic" }}>
                                        {rs.description}
                                    </p>
                                )}
                            </li>
                        ))}
                    </ul>
                )}
            </article>

            {error && (
                <article className={styles.panel} style={{ gridColumn: "1 / -1" }}>
                    <p className={styles.warning}>{error}</p>
                </article>
            )}
        </div>
    );
}
