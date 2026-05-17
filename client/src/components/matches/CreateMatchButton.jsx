import { FormPanel } from "@/components/forms/FormPanel.jsx";
import { FormPage }  from "@/components/forms/FormPage.jsx";
import { Field }     from "@/components/forms/Field.jsx";
import { PlusIcon }  from "@/components/icon/PlusIcon.jsx";
import { Spinner }   from "@/components/forms/Spinner.jsx";
import ItemCard      from "@/components/common/ItemCard.jsx";

import { useCreateMatch }        from "@/hooks/matches/useCreateMatch.js";
import { useCurrentUserContext } from "@/context/useCurrentUserContext.jsx";
import { useLangContext }        from "@/context/useLangContext.jsx";
import { usePageTexts }          from "@/hooks/common/usePageTexts.js";

import formStyles   from "@/style/common/Forms.module.css";
import commonStyles from "@/style/common/Common.module.css";
import panelStyles  from "@/style/common/Panel.module.css";
import buttonStyles from "@/style/common/Buttons.module.css";

// ---------------------------------------------------------------------------
// Client-side permission guard (mirrors server _can_manage_either_team logic)
// ---------------------------------------------------------------------------

/**
 * Returns true when the account can propose a match for at least one team.
 * Administrators and ClubOwners always pass; TeamManagers need at least one
 * entry in managedTeamIds.
 */
function canProposeMath(account) {
    if (!account) return false;
    const roles = account.roles ?? [];
    if (roles.includes("administrator")) return true;
    if (roles.includes("club_owner"))    return true;
    if (roles.includes("team_manager")) {
        return (account.managedTeamIds?.length ?? 0) > 0;
    }
    return false;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

/**
 * CreateMatchButton
 *
 * Self-contained trigger button + dropdown panel that walks the account
 * through a three-step wizard to propose a new match:
 *
 *   Step 0 - choose which managed team will be team1
 *   Step 1 - choose which ladder that team is registered in
 *   Step 2 - choose the opponent (team2) from the same ladder
 *   Step 3 - submit proposal
 *
 * Props
 * -----
 * managedTeams {Array<{ id, name, clubId, clubName, sportTypeId }>}
 *   Teams the current account can manage.  Comes from /api/teams/my.
 *
 * onCreated {(match: object) => void}
 *   Called after a successful POST /api/matches.
 *
 * theme {"light" | undefined}
 *   Forwarded to FormPanel for light/dark theming.
 */
export default function CreateMatchButton({ managedTeams = [], onCreated, theme }) {
    const { currentUser } = useCurrentUserContext();
    const { lang }        = useLangContext();
    const texts           = usePageTexts("matches", lang);

    const t = (key, fallback) => texts[key] ?? fallback;

    const {
        isOpen, isLoading, isSuccess, error,
        openPanel, closePanel,
        step, nextStep, prevStep, canNext,

        selectedTeamId,   setSelectedTeamId,
        ladders,          laddersLoading,  laddersError,
        selectedLadderId, setSelectedLadderId,
        peers,            peersLoading,    peersError,
        selectedPeerId,   setSelectedPeerId,
        submit,
    } = useCreateMatch({ managedTeams, onCreated });

    if (!canProposeMath(currentUser)) return null;
    if (managedTeams.length === 0)    return null;

    return (
        <FormPanel
            title={t("create_match_title", "Create Match")}
            triggerContent={
                <><PlusIcon rotated={isOpen} /> {t("create_match_btn", "New Match")}</>
            }
            triggerClassName={buttonStyles.createTeamTrigger}
            triggerOpenClassName={buttonStyles.createTeamTriggerOpen}
            panelClassName={buttonStyles.createTeamPanel}
            theme={theme}

            isOpen={isOpen}
            openPanel={openPanel}
            closePanel={closePanel}

            step={step}
            totalSteps={3}
            onNext={nextStep}
            onBack={prevStep}
            onSubmit={submit}

            isLoading={isLoading}
            isSuccess={isSuccess}
            successLabel={t("match_created", "Match proposal sent!")}
            error={error}

            submitLabel={t("create_match_submit", "Send Proposal")}
            canNext={canNext}
            ariaLabel={t("create_match_aria", "Create a new match proposal")}
        >

            <FormPage active={step === 0}>
                <Field label={t("create_match_your_team", "Your Team *")}>
                    <select
                        className={formStyles.formSelect}
                        value={selectedTeamId}
                        onChange={e => setSelectedTeamId(e.target.value)}
                        disabled={isLoading}
                        autoFocus
                    >
                        <option value="">
                            {t("create_match_select_team", "-- Select a team --")}
                        </option>
                        {managedTeams.map(team => (
                            <option key={team.id} value={team.id}>
                                {team.name}
                                {team.clubName ? ` (${team.clubName})` : ""}
                            </option>
                        ))}
                    </select>
                </Field>
            </FormPage>

            <FormPage active={step === 1}>
                {laddersLoading && (
                    <LoadingRow label={t("create_match_loading_ladders", "Loading ladders...")} />
                )}

                {!laddersLoading && laddersError && (
                    <p className={commonStyles.error}>{laddersError}</p>
                )}

                {!laddersLoading && !laddersError && ladders.length === 0 && (
                    <p className={commonStyles.muted}>
                        {t("create_match_no_ladders", "This team is not registered in any ladder.")}
                    </p>
                )}

                {!laddersLoading && !laddersError && ladders.length > 0 && (
                    <Field label={t("create_match_ladder", "Ladder *")}>
                        <select
                            className={formStyles.formSelect}
                            value={selectedLadderId}
                            onChange={e => setSelectedLadderId(e.target.value)}
                            disabled={isLoading}
                        >
                            <option value="">
                                {t("create_match_select_ladder", "-- Select a ladder --")}
                            </option>
                            {ladders.map(ladder => (
                                <option key={ladder.id} value={ladder.id}>
                                    {ladder.name || `Ladder #${ladder.id}`}
                                </option>
                            ))}
                        </select>
                    </Field>
                )}
            </FormPage>

            <FormPage active={step === 2}>
                {peersLoading && (
                    <LoadingRow label={t("create_match_loading_opponents", "Loading opponents...")} />
                )}

                {!peersLoading && peersError && (
                    <p className={commonStyles.error}>{peersError}</p>
                )}

                {!peersLoading && !peersError && peers.length === 0 && (
                    <p className={commonStyles.muted}>
                        {t("create_match_no_opponents", "No other teams in this ladder yet.")}
                    </p>
                )}

                {!peersLoading && !peersError && peers.length > 0 && (
                    <>
                        <p
                            className={commonStyles.muted}
                            style={{ fontSize: "0.8rem", marginBottom: "0.5rem" }}
                        >
                            {t("create_match_pick_opponent", "Choose an opponent:")}
                        </p>
                        <ul
                            className={panelStyles.list}
                            style={{ maxHeight: "260px", overflowY: "auto" }}
                        >
                            {peers.map(peer => (
                                <PeerCard
                                    key={peer.id}
                                    peer={peer}
                                    selected={String(selectedPeerId) === String(peer.id)}
                                    onSelect={() => setSelectedPeerId(peer.id)}
                                    selectLabel={t("create_match_select_btn", "Select")}
                                    selectedLabel={t("create_match_selected_btn", "Selected")}
                                />
                            ))}
                        </ul>
                    </>
                )}
            </FormPage>

        </FormPanel>
    );
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

/**
 * Inline spinner row shown while async data is loading inside the panel.
 */
function LoadingRow({ label }) {
    return (
        <div style={{ display: "flex", alignItems: "center", gap: "0.6rem", padding: "0.4rem 0" }}>
            <Spinner />
            <span className={commonStyles.muted} style={{ fontSize: "0.85rem" }}>{label}</span>
        </div>
    );
}

/**
 * Single opponent card rendered in the step-2 list.
 * Shows the team name, club, rank, and rating with a toggle-select button.
 */
function PeerCard({ peer, selected, onSelect, selectLabel, selectedLabel }) {
    return (
        <ItemCard>
            <div style={{ flex: 1, minWidth: 0 }}>
                <p
                    style={{
                        margin: 0,
                        fontWeight: 600,
                        fontSize: "0.9rem",
                        color: "#f1f5f9",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                    }}
                >
                    {peer.name}
                </p>
                <p style={{ margin: 0, fontSize: "0.78rem", color: "#94a3b8" }}>
                    {[
                        peer.clubName,
                        peer.rank   != null ? `#${peer.rank}`   : null,
                        peer.rating != null ? `${peer.rating} pts` : null,
                    ]
                        .filter(Boolean)
                        .join(" | ")}
                </p>
            </div>

            <button
                type="button"
                onClick={onSelect}
                aria-pressed={selected}
                aria-label={`${selected ? selectedLabel : selectLabel} ${peer.name}`}
                style={{
                    background:   selected
                        ? "rgba(56,189,248,0.22)"
                        : "rgba(56,189,248,0.07)",
                    border:       `1px solid ${selected
                        ? "rgba(56,189,248,0.6)"
                        : "rgba(56,189,248,0.24)"}`,
                    borderRadius: "0.5rem",
                    color:        "#38bdf8",
                    padding:      "0.28rem 0.7rem",
                    cursor:       "pointer",
                    fontSize:     "0.82rem",
                    fontWeight:   selected ? 700 : 500,
                    whiteSpace:   "nowrap",
                    flexShrink:   0,
                    transition:   "background 0.15s, border-color 0.15s",
                }}
            >
                {selected ? selectedLabel : selectLabel}
            </button>
        </ItemCard>
    );
}
