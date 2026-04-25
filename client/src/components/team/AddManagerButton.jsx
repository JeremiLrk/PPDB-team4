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

// Назви полів прав → ключ перекладу
const PERMISSION_KEYS = [
    { field: "canRename",       textKey: "perm_can_rename"        },
    { field: "canDelete",       textKey: "perm_can_delete"        },
    { field: "canEditPlayers",  textKey: "perm_can_edit_players"  },
    { field: "canEditManagers", textKey: "perm_can_edit_managers" },
];

const PERMISSION_FALLBACKS = {
    canRename:       "Rename team",
    canDelete:       "Delete team",
    canEditPlayers:  "Edit players",
    canEditManagers: "Edit managers",
};

/**
 * Перевірка can_edit_managers на фронтенді.
 * Відзеркалює логіку _can_edit_managers() на сервері:
 *   Administrator / ClubOwner — завжди true.
 *   TeamManager — перевіряємо account.managerPermissions?.[teamId]?.canEditManagers.
 *   Якщо ваш /api/me ще не повертає managerPermissions — fallback через managedTeamIds.
 */
function canEditManagers(account, team) {
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
        // Fallback: якщо managerPermissions недоступні — показуємо кнопку,
        // сервер однаково поверне 403 якщо права відсутні.
        return account.managedTeamIds?.includes(team.id) ?? false;
    }

    return false;
}

/**
 * AddManagerButton — dropdown-панель для пошуку та додавання менеджера команди.
 *
 * Props:
 *   teamId   {number|string}  — ID команди
 *   team     {object}         — об'єкт команди { id, clubId, … }
 *   onAdded  {() => void}     — колбек після успішного додавання
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

    // Рендеримо кнопку лише якщо поточний користувач може редагувати менеджерів
    if (!canEditManagers(currentUser, team)) return null;

    const t = (key, fallback) => texts[key] ?? fallback;

    return (
        <FormPanel
            title={t("add_manager_title", "Add Manager")}
            triggerContent={<><PlusIcon rotated={isOpen} /> {t("add_manager_btn", "Add Manager")}</>}

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
            successLabel={t("manager_added_success", "Manager added!")}

            submitLabel={t("confirm_add_manager", "Add Manager")}
            canNext={step === 1}

            error={addErr || searchErr || null}
            ariaLabel={t("add_manager_aria", "Add manager to team")}
            panelClassName={teamStyles.addPlayerPanel}
        >
            {/* ── Сторінка 0: пошук акаунту ── */}
            <FormPage active={step === 0}>

                <div className={teamStyles.searchRow}>
                    <input
                        ref={inputRef}
                        className={formStyles.formInput}
                        type="text"
                        placeholder={t("search_placeholder", "Name, email, or ID…")}
                        value={query}
                        onChange={e => setQuery(e.target.value)}
                    />
                    {searching && (
                        <span className={teamStyles.searchSpinner}><Spinner /></span>
                    )}
                </div>

                {!query.trim() && (
                    <p className={`${commonStyles.muted} ${teamStyles.noResults}`}>
                        {t("search_hint", "Type to search accounts.")}
                    </p>
                )}

                {!searching && !searchErr && query.trim() && results.length === 0 && (
                    <p className={`${commonStyles.muted} ${teamStyles.noResults}`}>
                        {t("no_results", "No accounts found.")}
                    </p>
                )}

                {results.length > 0 && (
                    <ul className={`${panelStyles.list} ${teamStyles.resultsList}`}>
                        {results.map(account => (
                            <SearchResultCard
                                key={account.id}
                                account={account}
                                selectLabel={t("select_btn", "Select")}
                                onSelect={() => selectAccount(account)}
                            />
                        ))}
                    </ul>
                )}
            </FormPage>

            {/* ── Сторінка 1: права нового менеджера ── */}
            <FormPage active={step === 1}>

                {selected && (
                    <SelectedAccountBadge
                        account={selected}
                        label={t("selected_account_label", "Adding as manager:")}
                    />
                )}

                <p className={`${commonStyles.muted} ${teamStyles.noResults}`}
                   style={{ marginBottom: "0.5rem" }}>
                    {t("permissions_label", "Permissions for this manager:")}
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

/* ── Sub-компоненти ──────────────────────────────────────────────────────── */

function SearchResultCard({ account, selectLabel, onSelect }) {
    const fullName = [account.firstName, account.lastName]
        .filter(Boolean).join(" ") || "-";

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
