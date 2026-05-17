// Team management UI component for AddManagerButton.

import commonStyles from "@/style/common/Common.module.css";
import formStyles   from "@/style/common/Forms.module.css";
import panelStyles  from "@/style/common/Panel.module.css";
import teamStyles   from "@/style/TeamSettings.module.css";

import { useAddManager }         from "@/hooks/teams/useAddManager.js";
import { useLangContext }         from "@/context/useLangContext.jsx";
import { usePageTexts }          from "@/hooks/common/usePageTexts.js";
import { PlusIcon }              from "@/components/icon/PlusIcon.jsx";
import { Spinner }               from "@/components/forms/Spinner.jsx";
import { FormPanel }             from "@/components/forms/FormPanel.jsx";
import { FormPage }              from "@/components/forms/FormPage.jsx";
import ItemCard                  from "@/components/common/ItemCard.jsx";
import { useCurrentUserContext } from "@/context/useCurrentUserContext.jsx";


const PERMISSION_KEYS = [
    { field: "canRename",       textKey: "perm_can_rename"        },
    { field: "canDelete",       textKey: "perm_can_delete"        },
    { field: "canEditPlayers",  textKey: "perm_can_edit_players"  },
    { field: "canEditManagers", textKey: "perm_can_edit_managers" },
];

const PERMISSION_FALLBACKS = {
    canRename:       "Team hernoemen",
    canDelete:       "Team verwijderen",
    canEditPlayers:  "Spelers beheren",
    canEditManagers: "Beheerders beheren",
};

/**
 * Checking can_edit_managers on the frontend.
 * Mirrors the logic of _can_edit_managers() on the server:
 * Administrator / ClubOwner — always true.
 * TeamManager — checking account.managerPermissions?.[teamId]?.canEditManagers.
 * If your /api/me doesn't yet return managerPermissions — fallback via managedTeamIds.
 */
function canEditManagers(account, team) {
    /*
     Checks whether the current account may manage manager permissions.
    */
    if (!account || !team) return false;
    const roles = account.roles ?? [];

    if (roles.includes("administrator")) return true;

    if (roles.includes("club_owner")) {
        const ownsClub    = team.clubId && account.clubIds?.includes(team.clubId);
        const managesTeam = account.managedTeamIds?.includes(team.id);
        return ownsClub || managesTeam;
    }

    if (roles.includes("team_manager")) {
        const perms = account.managerPermissions?.[team.id];
        if (perms !== undefined) return perms.canEditManagers;
        // Fallback: if managerPermissions are not available — show the button,
        // the server will still return 403 if the permissions are missing.
        return account.managedTeamIds?.includes(team.id) ?? false;
    }

    return false;
}

/**
 * AddManagerButton — dropdown panel for searching and adding a team manager.
 *
 * Props:
 * teamId {number|string} — Team ID
 * team {object} — Team object { id, clubId, … }
 * onAdded {() => void} — Callback after successful addition
 */
export default function AddManagerButton({ teamId, team, onAdded }) {
    const { currentUser } = useCurrentUserContext();
    const { lang }        = useLangContext();
    const texts           = usePageTexts("team_settings", lang);

    const {
        isOpen, openPanel, closePanel,
        step,
        query, setQuery,
        results, searching, searchErr,
        selected, selectAccount, goBack,
        permissions, togglePermission,
        submit, addingId, addErr,
        isSuccess,
        inputRef,
    } = useAddManager({ teamId, onAdded });

    // Render the button only if the current user can edit managers
    if (!canEditManagers(currentUser, team)) return null;

    const t = (key, fallback) => texts[key] ?? fallback;
    /*
     Renders the manager add wizard only for users with permission.
    */

    return (
        <FormPanel
            title={t("add_manager_title", "Beheerder toevoegen")}
            triggerContent={<><PlusIcon rotated={isOpen} /> {t("add_manager_btn", "Beheerder toevoegen")}</>}

            isOpen={isOpen}
            openPanel={openPanel}
            closePanel={closePanel}

            step={step}
            totalSteps={2}
            onNext={null}
            onBack={step === 1 ? goBack : null}
            onSubmit={step === 1 ? submit : null}

            isLoading={!!addingId}
            isSuccess={isSuccess}
            successLabel={t("manager_added_success", "Beheerder toegevoegd!")}

            submitLabel={t("confirm_add_manager", "Beheerder toevoegen")}
            canNext={step === 1}

            error={addErr ? (texts[addErr] ?? addErr) : (searchErr || null)}
            ariaLabel={t("add_manager_aria", "Beheerder aan team toevoegen")}
            panelClassName={teamStyles.addPlayerPanel}
        >
            {/* ── Page 0: account search ── */}
            <FormPage active={step === 0}>

                <div className={teamStyles.searchRow}>
                    <input
                        ref={inputRef}
                        className={formStyles.formInput}
                        type="text"
                        placeholder={t("search_placeholder", "Naam, e-mail of ID…")}
                        value={query}
                        onChange={e => setQuery(e.target.value)}
                    />
                    {searching && (
                        <span className={teamStyles.searchSpinner}><Spinner /></span>
                    )}
                </div>

                {!query.trim() && (
                    <p className={`${commonStyles.muted} ${teamStyles.noResults}`}>
                        {t("search_hint", "Typ om accounts te zoeken.")}
                    </p>
                )}

                {!searching && !searchErr && query.trim() && results.length === 0 && (
                    <p className={`${commonStyles.muted} ${teamStyles.noResults}`}>
                        {t("no_results", "Geen accounts gevonden.")}
                    </p>
                )}

                {results.length > 0 && (
                    <ul className={`${panelStyles.list} ${teamStyles.resultsList}`}>
                        {results.map(account => (
                            <SearchResultCard
                                key={account.id}
                                account={account}
                                selectLabel={t("select_btn", "Selecteren")}
                                onSelect={() => selectAccount(account)}
                            />
                        ))}
                    </ul>
                )}
            </FormPage>

            {/* ── Page 1: new manager rights ── */}
            <FormPage active={step === 1}>

                {selected && (
                    <SelectedAccountBadge
                        account={selected}
                        label={t("selected_account_label", "Wordt toegevoegd als beheerder:")}
                    />
                )}

                <p className={`${commonStyles.muted} ${teamStyles.noResults}`}
                   style={{ marginBottom: "0.5rem" }}>
                    {t("permissions_label", "Rechten voor deze beheerder:")}
                </p>

                <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
                    {PERMISSION_KEYS.map(({ field, textKey }) => (
                        <li key={field} style={{ padding: "0.35rem 0" }}>
                            <label style={{
                                display:     "flex",
                                alignItems:  "center",
                                gap:         "0.65rem",
                                cursor:      "pointer",
                                userSelect:  "none",
                            }}>
                                <input
                                    type="checkbox"
                                    checked={permissions[field]}
                                    onChange={() => togglePermission(field)}
                                    style={{ accentColor: "#38bdf8", width: "1rem", height: "1rem" }}
                                />
                                <span className={commonStyles.primaryText}>
                                    {t(textKey, PERMISSION_FALLBACKS[field])}
                                </span>
                            </label>
                        </li>
                    ))}
                </ul>

            </FormPage>
        </FormPanel>
    );
}

/* ── Sub-components ──────────────────────────────────────────────────────── */

function SearchResultCard({ account, selectLabel, onSelect }) {
    const fullName = [account.firstName, account.lastName]
        .filter(Boolean).join(" ") || "-";
    /*
     Renders one selectable account result.
    */

    return (
        <ItemCard>
            <div style={{ flex: 1, minWidth: 0 }}>
                <p style={{ margin: 0, fontWeight: 600, fontSize: "0.9rem", color: "#f1f5f9" }}>
                    {fullName}
                </p>
                <p style={{ margin: 0, fontSize: "0.78rem", color: "#94a3b8" }}>
                    {account.email}
                </p>
            </div>
            <button
                onClick={onSelect}
                aria-label={`${selectLabel} ${fullName}`}
                style={{
                    background:   "rgba(56,189,248,0.12)",
                    border:       "1px solid rgba(56,189,248,0.28)",
                    borderRadius: "0.5rem",
                    color:        "#38bdf8",
                    padding:      "0.25rem 0.75rem",
                    cursor:       "pointer",
                    fontSize:     "0.82rem",
                    whiteSpace:   "nowrap",
                    flexShrink:   0,
                }}
            >
                {selectLabel} →
            </button>
        </ItemCard>
    );
}

function SelectedAccountBadge({ account, label }) {
    const fullName = [account.firstName, account.lastName]
        .filter(Boolean).join(" ") || "-";
    /*
     Renders the chosen account before permissions are confirmed.
    */

    return (
        <div style={{
            display:      "flex",
            alignItems:   "center",
            gap:          "0.6rem",
            background:   "rgba(56,189,248,0.07)",
            border:       "1px solid rgba(56,189,248,0.2)",
            borderRadius: "0.65rem",
            padding:      "0.55rem 0.9rem",
            marginBottom: "1rem",
        }}>
            <span style={{ fontSize: "1.1rem" }}>👤</span>
            <div style={{ flex: 1, minWidth: 0 }}>
                {label && (
                    <p style={{ margin: 0, fontSize: "0.72rem", color: "#64748b" }}>{label}</p>
                )}
                <p style={{ margin: 0, fontWeight: 600, fontSize: "0.88rem", color: "#f1f5f9" }}>
                    {fullName}
                </p>
                <p style={{ margin: 0, fontSize: "0.76rem", color: "#94a3b8" }}>
                    {account.email}
                </p>
            </div>
        </div>
    );
}
