import { useState } from "react";
import { useSportTypes } from "@/hooks/useSportTypes"; 
import styles from "@/style/ClubSettings.module.css";

export function ClubLadders({ 
    ladders = [], 
    onCreate, 
    ratingFunctions = [], 
    ruleSets = [], 
    teams = [], 
    onAddTeam, 
    texts = {} 
}) {
    const { sportTypes } = useSportTypes();

    // --- State for Creating a New Ladder ---
    const [form, setForm] = useState({
        name: "",
        description: "",
        sport_type_id: "",
        rule_set_id: "",
        ladder_rating_function_id: ""
    });
    const [submitting, setSubmitting] = useState(false);

    // --- State for Adding a Team to a Ladder ---
    const [ladderSearch, setLadderSearch] = useState("");
    const [teamSearch, setTeamSearch] = useState("");
    const [selectedLadderId, setSelectedLadderId] = useState("");
    const [selectedTeamId, setSelectedTeamId] = useState("");
    const [addingTeam, setAddingTeam] = useState(false);

    // Filtered lists for the search/dropdowns
    const filteredLadders = ladders.filter(l => 
        l.name.toLowerCase().includes(ladderSearch.toLowerCase())
    );
    const filteredTeams = teams.filter(t => 
        t.name.toLowerCase().includes(teamSearch.toLowerCase())
    );

    // --- Handlers for Creation ---
    const handleChange = (e) => {
        setForm(prev => ({
            ...prev,
            [e.target.name]: e.target.value
        }));
    };

    const handleCreate = async () => {
        if (!form.name.trim() || !form.sport_type_id || !form.rule_set_id || !form.ladder_rating_function_id) {
            alert(texts.fill_all_required_fields || "Vul alle verplichte velden in.");
            return;
        }

        setSubmitting(true);
        await onCreate({
            ...form,
            sport_type_id: Number(form.sport_type_id),
            ruleset_id: Number(form.rule_set_id),
            ladder_rating_function_id: Number(form.ladder_rating_function_id)
        });

        setForm({ name: "", description: "", sport_type_id: "", rule_set_id: "", ladder_rating_function_id: "" });
        setSubmitting(false);
    };

    // --- Handler for Adding Team ---
    const handleAddTeamSubmit = async () => {
        if (!selectedLadderId || !selectedTeamId) {
            alert(texts.select_ladder_and_team || "Selecteer een ladder en een team.");
            return;
        }

        setAddingTeam(true);
        try {
            await onAddTeam(selectedLadderId, selectedTeamId);
            // Reset selection after success
            setSelectedTeamId("");
            setTeamSearch("");
        } catch (err) {
            console.error("Failed to add team:", err);
        } finally {
            setAddingTeam(false);
        }
    };

    return (
        <div className={`${styles.contentGrid} ${styles.contentFade}`}>
            {/* PANEL 1: CREATE LADDER */}
            <article className={styles.panel}>
                <h3 className={styles.panelTitle}>{texts.ladder_create_title || "Ladder aanmaken"}</h3>

                <div className={styles.form}>
                    <input
                        className={styles.formInput}
                        name="name"
                        placeholder={texts.ladder_name_placeholder || "Laddernaam"}
                        value={form.name}
                        onChange={handleChange}
                    />

                    <select className={styles.formInput} name="sport_type_id" value={form.sport_type_id} onChange={handleChange}>
                        <option value="" disabled>{texts.choose_sport_type || "Kies een sporttype"}</option>
                        {sportTypes.map(s => (
                            <option key={s.id} value={s.id}>{s.name}</option>
                        ))}
                    </select>

                    <select className={styles.formInput} name="rule_set_id" value={form.rule_set_id} onChange={handleChange}>
                        <option value="" disabled>{texts.choose_rule_set || "Kies een regelset"}</option>
                        {ruleSets.map(r => (
                            <option key={r.id} value={r.id}>{r.name}</option>
                        ))}
                    </select>

                    <select className={styles.formInput} name="ladder_rating_function_id" value={form.ladder_rating_function_id} onChange={handleChange}>
                        <option value="" disabled>{texts.choose_rating_function || "Kies ratingsysteem"}</option>
                        {ratingFunctions.map(rf => (
                            <option key={rf.id} value={rf.id}>{rf.name}</option>
                        ))}
                    </select>

                    <textarea
                        className={styles.formTextarea}
                        name="description"
                        placeholder={texts.ladder_description_placeholder || "Omschrijving"}
                        value={form.description}
                        onChange={handleChange}
                        rows={3}
                    />

                    <button
                        className={styles.submitButton}
                        onClick={handleCreate}
                        disabled={submitting}
                    >
                        {submitting ? (texts.creating_ladder || "Aanmaken...") : (texts.create_ladder || "Ladder aanmaken")}
                    </button>
                </div>
            </article>

            {/* PANEL 2: ADD TEAM TO LADDER (Searchable) */}
            <article className={styles.panel}>
                <h3 className={styles.panelTitle}>{texts.add_team_title || "Team toevoegen aan ladder"}</h3>
                
                <div className={styles.form}>
                    <p className={styles.secondaryText}>Search for a ladder and a team to link them.</p>
                    
                    {/* Ladder Selection */}
                    <input 
                        className={styles.formInput}
                        placeholder={texts.search_ladder || "Zoek ladder..."}
                        value={ladderSearch}
                        onChange={(e) => setLadderSearch(e.target.value)}
                    />
                    <select 
                        className={styles.formInput}
                        value={selectedLadderId}
                        onChange={(e) => setSelectedLadderId(e.target.value)}
                    >
                        <option value="" disabled>{texts.select_ladder || "Selecteer een ladder"}</option>
                        {filteredLadders.map(l => (
                            <option key={l.id} value={l.id}>{l.name}</option>
                        ))}
                    </select>

                    <hr className={styles.divider} />

                    {/* Team Selection */}
                    <input 
                        className={styles.formInput}
                        placeholder={texts.search_team || "Zoek team..."}
                        value={teamSearch}
                        onChange={(e) => setTeamSearch(e.target.value)}
                    />
                    <select 
                        className={styles.formInput}
                        value={selectedTeamId}
                        onChange={(e) => setSelectedTeamId(e.target.value)}
                    >
                        <option value="" disabled>{texts.select_team || "Selecteer een team"}</option>
                        {filteredTeams.map(t => (
                            <option key={t.id} value={t.id}>{t.name}</option>
                        ))}
                    </select>

                    <button 
                        className={styles.submitButton}
                        onClick={handleAddTeamSubmit}
                        disabled={!selectedLadderId || !selectedTeamId || addingTeam}
                    >
                        {addingTeam ? (texts.adding_team || "Toevoegen...") : (texts.add_team || "Team Toevoegen")}
                    </button>
                </div>
            </article>

            {/* PANEL 3: EXISTING LADDERS LIST */}
            <article className={styles.panel}>
                <h3 className={styles.panelTitle}>{texts.ladders_title || "Ladders"}</h3>

                {ladders.length === 0 ? (
                    <p className={styles.muted}>{texts.no_ladders || "Nog geen ladders."}</p>
                ) : (
                    <ul className={styles.list}>
                        {ladders.map(l => (
                            <li key={l.id} className={styles.listItem}>
                                <div>
                                    <p className={styles.primaryText}>{l.name}</p>
                                    <p className={styles.secondaryText}>
                                        {l.description || texts.no_ladder_description || "Geen omschrijving"}
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