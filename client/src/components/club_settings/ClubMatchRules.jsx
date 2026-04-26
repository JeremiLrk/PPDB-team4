import { useCallback, useEffect, useState } from "react";
import styles from "@/style/ClubSettings.module.css";

const EMPTY_RULE_FORM = {
    name: "",
    description: "",
    canBeUsedByOthers: true,
};

const EMPTY_RULESET_FORM = {
    name: "",
    description: "",
    canBeUsedByOthers: true,
};

function normalizeList(payload, key) {
    if (!payload) return [];
    if (Array.isArray(payload)) return payload;
    if (Array.isArray(payload[key])) return payload[key];
    return [];
}

export default function ClubMatchRules({ clubId, texts = {} }) {
    const [rules, setRules] = useState([]);
    const [ruleSets, setRuleSets] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [submitting, setSubmitting] = useState(false);
    const [selectedRuleIds, setSelectedRuleIds] = useState([]);
    const [ruleForm, setRuleForm] = useState(EMPTY_RULE_FORM);
    const [ruleSetForm, setRuleSetForm] = useState(EMPTY_RULESET_FORM);

    const fetchData = useCallback(async () => {
        setLoading(true);
        setError("");
        try {
            const [rulesRes, ruleSetsRes] = await Promise.all([
                fetch("/api/match-rules?from=0&to=200", { credentials: "include" }),
                fetch("/api/match-rule-sets?from=0&to=200", { credentials: "include" }),
            ]);

            const rulesData = await rulesRes.json().catch(() => ({}));
            const ruleSetsData = await ruleSetsRes.json().catch(() => ({}));

            if (!rulesRes.ok) {
                throw new Error(rulesData?.message || texts.could_not_load_rules || "Regels konden niet worden geladen.");
            }
            if (!ruleSetsRes.ok) {
                throw new Error(ruleSetsData?.message || texts.could_not_load_rules || "Regelsets konden niet worden geladen.");
            }

            setRules(normalizeList(rulesData, "rules"));
            setRuleSets(normalizeList(ruleSetsData, "ruleSets"));
        } catch (err) {
            setError(err?.message || texts.could_not_load_rules || "Regels konden niet worden geladen.");
        } finally {
            setLoading(false);
        }
    }, [texts]);

    useEffect(() => {
        void fetchData();
    }, [fetchData]);

    function updateRuleForm(field, value) {
        setRuleForm(prev => ({ ...prev, [field]: value }));
    }

    function updateRuleSetForm(field, value) {
        setRuleSetForm(prev => ({ ...prev, [field]: value }));
    }

    function toggleRuleSelection(ruleId) {
        setSelectedRuleIds(prev =>
            prev.includes(ruleId)
                ? prev.filter(id => id !== ruleId)
                : [...prev, ruleId],
        );
    }

    async function createRule() {
        const name = ruleForm.name.trim();
        const description = ruleForm.description.trim();
        if (!name) return;

        setSubmitting(true);
        setError("");

        try {
            const res = await fetch("/api/match-rules", {
                method: "POST",
                credentials: "include",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    name,
                    description,
                    canBeUsedByOthers: ruleForm.canBeUsedByOthers,
                    clubId: clubId ? Number(clubId) : null,
                }),
            });

            const data = await res.json().catch(() => ({}));
            if (!res.ok) {
                throw new Error(data?.message || texts.could_not_create_rule || "Regel kon niet worden aangemaakt.");
            }

            setRuleForm(EMPTY_RULE_FORM);
            await fetchData();
        } catch (err) {
            setError(err?.message || texts.could_not_create_rule || "Regel kon niet worden aangemaakt.");
        } finally {
            setSubmitting(false);
        }
    }

    async function createRuleSet() {
        const name = ruleSetForm.name.trim();
        const description = ruleSetForm.description.trim();
        if (!name) return;

        setSubmitting(true);
        setError("");

        try {
            const res = await fetch("/api/match-rule-sets", {
                method: "POST",
                credentials: "include",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    name,
                    description,
                    canBeUsedByOthers: ruleSetForm.canBeUsedByOthers,
                    clubId: clubId ? Number(clubId) : null,
                }),
            });

            const data = await res.json().catch(() => ({}));
            if (!res.ok) {
                throw new Error(data?.message || texts.could_not_create_rule_set || "Regelset kon niet worden aangemaakt.");
            }

            const createdRuleSetId = data?.ruleSet?.id;
            if (createdRuleSetId && selectedRuleIds.length > 0) {
                for (const ruleId of selectedRuleIds) {
                    const attachRes = await fetch(`/api/match-rule-sets/${createdRuleSetId}/rules`, {
                        method: "POST",
                        credentials: "include",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ ruleId }),
                    });
                    const attachData = await attachRes.json().catch(() => ({}));
                    if (!attachRes.ok) {
                        throw new Error(attachData?.message || texts.could_not_attach_rule || "Regel kon niet aan de set worden gekoppeld.");
                    }
                }
            }

            setRuleSetForm(EMPTY_RULESET_FORM);
            setSelectedRuleIds([]);
            await fetchData();
        } catch (err) {
            setError(err?.message || texts.could_not_create_rule_set || "Regelset kon niet worden aangemaakt.");
        } finally {
            setSubmitting(false);
        }
    }

    if (loading) {
        return (
            <div className={`${styles.contentGrid} ${styles.contentFade}`}>
                <article className={styles.panel}>
                    <h3 className={styles.panelTitle}>{texts.rules_loading_title || "Wedstrijdregels"}</h3>
                    <p className={styles.muted}>{texts.rules_loading_text || "Regels laden..."}</p>
                </article>
            </div>
        );
    }

    return (
        <div className={`${styles.contentGrid} ${styles.contentFade}`}>
            <article className={styles.panel}>
                <h3 className={styles.panelTitle}>{texts.rules_library_title || "Regelbibliotheek"}</h3>

                <div className={styles.form}>
                    <input
                        className={styles.formInput}
                        placeholder={texts.rule_name_placeholder || "Regelnaam"}
                        value={ruleForm.name}
                        onChange={(e) => updateRuleForm("name", e.target.value)}
                    />
                    <textarea
                        className={styles.formTextarea}
                        placeholder={texts.rule_description_placeholder || "Omschrijving"}
                        value={ruleForm.description}
                        onChange={(e) => updateRuleForm("description", e.target.value)}
                        rows={3}
                    />
                    <label className={styles.secondaryText} style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
                        <input
                            type="checkbox"
                            checked={ruleForm.canBeUsedByOthers}
                            onChange={(e) => updateRuleForm("canBeUsedByOthers", e.target.checked)}
                        />
                        {texts.use_by_others || "Door anderen te gebruiken"}
                    </label>
                    <button
                        className={styles.submitButton}
                        onClick={createRule}
                        disabled={submitting}
                        type="button"
                    >
                        {submitting ? (texts.adding_rule || "Bezig met aanmaken...") : (texts.add_rule || "Regel toevoegen")}
                    </button>
                </div>

                <div className="mt-6">
                    <h4 className={styles.secondaryText}>{texts.available_rules || "Beschikbare regels"}</h4>
                    <ul className={styles.list} style={{ marginTop: "10px" }}>
                        {rules.map(rule => (
                            <li key={rule.id} className={styles.listItem} style={{ padding: "8px" }}>
                                <div>
                                    <p className={styles.primaryText} style={{ fontSize: "0.9rem" }}>
                                        {rule.name}
                                    </p>
                                    {rule.description && (
                                        <p className={styles.secondaryText} style={{ fontSize: "0.8rem" }}>
                                            {rule.description}
                                        </p>
                                    )}
                                </div>
                            </li>
                        ))}
                        {rules.length === 0 && (
                            <li className={styles.listItem} style={{ padding: "8px" }}>
                                <p className={styles.secondaryText}>{texts.no_rules || "Nog geen regels."}</p>
                            </li>
                        )}
                    </ul>
                </div>
            </article>

            <article className={styles.panel}>
                <h3 className={styles.panelTitle}>{texts.build_rule_set_title || "Regelset samenstellen"}</h3>

                <div className={styles.form}>
                    <input
                        className={styles.formInput}
                        placeholder={texts.rule_set_name_placeholder || "Naam van regelset"}
                        value={ruleSetForm.name}
                        onChange={(e) => updateRuleSetForm("name", e.target.value)}
                    />
                    <textarea
                        className={styles.formTextarea}
                        placeholder={texts.rule_description_placeholder || "Omschrijving"}
                        value={ruleSetForm.description}
                        onChange={(e) => updateRuleSetForm("description", e.target.value)}
                        rows={3}
                    />
                    <label className={styles.secondaryText} style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
                        <input
                            type="checkbox"
                            checked={ruleSetForm.canBeUsedByOthers}
                            onChange={(e) => updateRuleSetForm("canBeUsedByOthers", e.target.checked)}
                        />
                        Door anderen te gebruiken
                    </label>
                    <div className="my-4" style={{ maxHeight: "220px", overflowY: "auto" }}>
                        <p className={styles.secondaryText} style={{ marginBottom: "8px" }}>
                        {texts.select_rules || "Selecteer regels om op te nemen"}
                        </p>
                        {rules.map(rule => (
                            <label
                                key={rule.id}
                                style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "8px", cursor: "pointer" }}
                            >
                                <input
                                    type="checkbox"
                                    checked={selectedRuleIds.includes(rule.id)}
                                    onChange={() => toggleRuleSelection(rule.id)}
                                />
                                <span className={styles.primaryText} style={{ fontSize: "0.85rem" }}>
                                    {rule.name}
                                </span>
                            </label>
                        ))}
                    </div>
                    <button
                        className={styles.submitButton}
                        onClick={createRuleSet}
                        disabled={submitting}
                        type="button"
                    >
                        {submitting ? (texts.saving_rule_set || "Bezig met opslaan...") : (texts.save_rule_set || "Regelset opslaan")}
                    </button>
                </div>

                <div className="mt-6">
                    <h4 className={styles.secondaryText}>{texts.existing_rule_sets || "Bestaande regelsets"}</h4>
                    <ul className={styles.list} style={{ marginTop: "10px" }}>
                        {ruleSets.map(ruleSet => (
                            <li
                                key={ruleSet.id}
                                className={styles.listItem}
                                style={{ padding: "8px", flexDirection: "column", alignItems: "flex-start" }}
                            >
                                <p className={styles.primaryText}>{ruleSet.name}</p>
                                <p className={styles.secondaryText} style={{ fontSize: "0.75rem" }}>
                                    {texts.contains_rules || "Bevat"} {ruleSet.rules?.length || 0} {texts.rules_count_suffix || "regels"}
                                </p>
                                {ruleSet.description && (
                                    <p className={styles.secondaryText} style={{ fontSize: "0.75rem" }}>
                                        {ruleSet.description}
                                    </p>
                                )}
                            </li>
                        ))}
                        {ruleSets.length === 0 && (
                            <li className={styles.listItem} style={{ padding: "8px" }}>
                                <p className={styles.secondaryText}>{texts.no_rule_sets || "Nog geen regelsets."}</p>
                            </li>
                        )}
                    </ul>
                </div>
            </article>

            {error && (
                <article className={styles.panel} style={{ gridColumn: "1 / -1" }}>
                    <p className={styles.warning}>{error}</p>
                </article>
            )}
        </div>
    );
}
