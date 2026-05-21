// Regression tests for settings.flow.test.

import "@testing-library/jest-dom/vitest";
import React from "react";
import { beforeEach, describe, expect, test, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";

import { LangContext } from "../src/context/useLangContext.jsx";
import CurrentUserContext from "../src/context/useCurrentUserContext.jsx";
import { ThemeContext } from "../src/context/useThemeContext.jsx";
import ClubDisputedMatchesPage from "../src/pages/ClubDisputedMatchesPage.jsx";
import ClubSidebar from "../src/components/club_settings/ClubSidebar.jsx";
import ClubLadders from "../src/components/club_settings/ClubLadders.jsx";
import ClubMatchRules from "../src/components/club_settings/ClubMatchRules.jsx";
import Ladder from "../src/pages/Ladder.jsx";
import AddPlayerButton from "../src/components/team/AddPlayerButton.jsx";
import AddManagerButton from "../src/components/team/AddManagerButton.jsx";

const clubSettingsTextState = vi.hoisted(() => ({
    sidebar_title: "Settings",
    tab_general: "General info",
    tab_ladders: "Ladders",
    tab_members: "Members",
    tab_rules: "Match rules",
    tab_owners: "Owners",
    tab_disputed: "Disputed matches",
    tab_home: "Go to club home",
    loading: "Loading...",
    disputed_title: "Disputed matches",
    disputed_description: "Matches where both teams submitted conflicting scores.",
    disputed_queue_title: "Dispute queue",
    no_disputed: "No disputed matches at this time.",
    retry: "Retry",
    select_match_prompt: "Select a disputed match from the list to review and adjudicate it.",
    submitted_scores: "Submitted scores",
    ladder_label: "Ladder",
    ruleset_label: "Rule set",
    rules_snapshot_title: "Rules in effect",
    adjudicate_title: "Submit decisive score",
    submit_decisive_score: "Submit decisive score",
    submitting: "Submitting...",
    ladder_admin_label: "Ladder admin",
    no_ladder: "No ladder",
    no_ruleset: "None",
    back: "Back to settings",
    disputed_forbidden: "You do not have permission to view or adjudicate disputed matches.",
    create_rule_set_title: "Nieuwe regelset",
    rule_set_name_placeholder: "Naam van de regelset",
    rule_description_placeholder: "Omschrijving (optioneel)",
    match_format_label: "Wedstrijdformaat",
    third_set_label: "Derde set bij 1-1 stand",
    deuce_rule_label: "40-40 regel (Deuce)",
    game_format_label: "Spelvorm",
    use_by_others: "Door anderen te gebruiken",
    save_rule_set: "Regelset opslaan",
    saving_rule_set: "Bezig met opslaan...",
    existing_rule_sets: "Bestaande regelsets",
    no_rule_sets: "Nog geen regelsets.",
    delete: "Verwijder",
}));

const ladderTextState = vi.hoisted(() => ({
    back_to_club: "Back to club",
    ladder_rankings: "Ladder Rankings",
    ruleset_label: "Ruleset",
    system_label: "System",
    loading_rankings: "Loading rankings...",
    no_players: "No players in this ladder yet.",
    rank: "Rank",
    player: "Player",
    rating: "Rating",
}));

const clubSettingsHookState = vi.hoisted(() => ({
    loading: false,
}));

const disputedHookState = vi.hoisted(() => ({
    matches: [],
    total: 0,
    loading: false,
    error: null,
    forbidden: false,
    reload: vi.fn(),
}));

const ladderHookState = vi.hoisted(() => ({
    ladder: null,
    players: [],
}));

const rulesState = vi.hoisted(() => ({
    ruleSets: [],
    nextRuleId: 3,
}));

const sportTypesState = vi.hoisted(() => ({
    sportTypes: [],
}));

const addPlayerState = vi.hoisted(() => ({
    searchHits: [
        {
            id: 91,
            firstName: "Alice",
            lastName: "Runner",
            email: "alice.runner@example.com",
        },
    ],
    addCalls: 0,
}));

vi.mock("../src/hooks/common/usePageTexts.js", () => ({
    usePageTexts: (page) => {
        if (page === "club_settings") return clubSettingsTextState;
        if (page === "ladder") return ladderTextState;
        return {};
    },
}));

vi.mock("../src/hooks/useClubSettings.js", () => ({
    useClubSettings: () => clubSettingsHookState,
}));

vi.mock("../src/hooks/useSportTypes.js", () => ({
    useSportTypes: () => sportTypesState,
}));

vi.mock("../src/hooks/matches/useDisputedMatches.js", () => ({
    useDisputedMatches: () => disputedHookState,
}));

vi.mock("../src/hooks/useLadder.js", () => ({
    useLadder: () => ({
        ladder: ladderHookState.ladder,
        loading: false,
        error: null,
    }),
    useLadderPlayers: () => ({
        players: ladderHookState.players,
        loading: false,
        error: null,
    }),
}));
// Shared test helper for arranging the scenario under test.

function jsonResponse(data, status = 200) {
    return {
        ok: status >= 200 && status < 300,
        status,
        json: async () => JSON.parse(JSON.stringify(data)),
    };
}

function renderWithLang(ui, { lang = "en", route = "/" } = {}) {
    return render(
        <MemoryRouter initialEntries={[route]}>
            <LangContext.Provider value={{ lang, setLang: () => {} }}>
                {ui}
            </LangContext.Provider>
        </MemoryRouter>,
    );
}

function getFetchCall(url, method) {
    return global.fetch.mock.calls.find(([callUrl, callInit]) => {
        if (callUrl !== url) return false;
        return (callInit?.method || "GET").toUpperCase() === method;
    });
}

beforeEach(() => {
    clubSettingsHookState.loading = false;
    disputedHookState.matches = [];
    disputedHookState.total = 0;
    disputedHookState.loading = false;
    disputedHookState.error = null;
    disputedHookState.forbidden = false;
    disputedHookState.reload.mockReset();

    ladderHookState.ladder = null;
    ladderHookState.players = [];

    rulesState.ruleSets = [
        {
            id: 1,
            name: "Standard Ladder",
            description: "Default ladder rules",
            matchFormat: "best_of_3",
            thirdSetFormat: "super_tiebreak",
            deuceRule: "advantage",
            gameFormat: "doubles",
            creatorId: 7,
        },
    ];
    rulesState.nextRuleId = 3;
    sportTypesState.sportTypes = [
        { id: 1, name: "Tennis", maxPlayers: 1 },
        { id: 2, name: "Basketball", maxPlayers: 5 },
    ];
    addPlayerState.searchHits = [
        {
            id: 91,
            firstName: "Alice",
            lastName: "Runner",
            email: "alice.runner@example.com",
        },
    ];
    addPlayerState.addCalls = 0;

    global.fetch = vi.fn(async (input, init = {}) => {
        const rawUrl = typeof input === "string" ? input : input.url;
        const method = (init.method || (typeof input === "string" ? "GET" : input.method) || "GET").toUpperCase();
        const url = new URL(rawUrl, "http://localhost");
        const path = url.pathname;
        const body = typeof init.body === "string" && init.body.length > 0 ? JSON.parse(init.body) : null;

        if (path === "/api/match-rule-sets" && method === "GET") {
            return jsonResponse({ ruleSets: rulesState.ruleSets });
        }

        if (path === "/api/match-rule-sets" && method === "POST") {
            const ruleSet = {
                id: rulesState.nextRuleId++,
                ...body,
            };
            rulesState.ruleSets = [...rulesState.ruleSets, ruleSet];
            return jsonResponse({ ruleSet });
        }

        if (path === "/api/teams/77/players/search" && method === "GET") {
            return jsonResponse({ results: addPlayerState.searchHits });
        }

        if (path === "/api/teams/77/players" && method === "POST") {
            addPlayerState.addCalls += 1;
            if (addPlayerState.addCalls === 1) {
                return jsonResponse({
                    message: "Adding this player would exceed the maximum roster size in one or more ladders.",
                    warning: "exceeds_max_players",
                    ladders: [{ id: 12, name: "Demo Ladder" }],
                    requireConfirm: true,
                }, 202);
            }
            return jsonResponse({
                message: "Player join request created successfully.",
                request: {
                    id: 123,
                    teamId: 77,
                    userId: 91,
                    status: "pending",
                },
            }, 201);
        }

        if (path === "/api/matches/55/score" && method === "POST") {
            ladderHookState.players = [
                { id: 1, name: "Topspin Tigers", rating: 1020 },
                { id: 2, name: "Court Kings", rating: 980 },
            ];
            return jsonResponse({
                finalized: true,
                resolvedScore: { scoreTeam1: 2, scoreTeam2: 1 },
            });
        }

        return jsonResponse({ message: `Unexpected fetch in test: ${path}` }, 404);
    });
});
// End-to-end or flow coverage for the main user journey in this file.

describe("Disputed matches and rulesets", () => {
    // Verifies the confirm flow retries the add-player request with ladder consent.
    test("team settings add-player confirm button retries with ladder confirmation", async () => {
        const user = userEvent.setup();
        const onAdded = vi.fn();

        renderWithLang(<AddPlayerButton teamId={77} onAdded={onAdded} />, { route: "/clubs/1/settings/members" });

        await user.click(screen.getByRole("button", { name: "Add Player" }));
        await user.type(screen.getByPlaceholderText("Name, email, or ID..."), "Alice");

        expect(await screen.findByRole("button", { name: "Add Alice Runner" })).toBeInTheDocument();
        await user.click(screen.getByRole("button", { name: "Add Alice Runner" }));

        expect(await screen.findByText("Adding this player would exceed the maximum roster size in one or more ladders.")).toBeInTheDocument();
        await user.click(screen.getByRole("button", { name: "Remove from ladders and add" }));

        await waitFor(() => expect(onAdded).toHaveBeenCalledTimes(1));
        expect(global.fetch).toHaveBeenCalledWith(
            "/api/teams/77/players",
            expect.objectContaining({
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ accountId: 91, confirmDropLadders: true }),
            }),
        );
    });

    // Verifies the manager panel still opens cleanly in light mode.
    test("team settings add-manager panel opens in light mode", async () => {
        const user = userEvent.setup();

        render(
            <MemoryRouter initialEntries={["/clubs/1/settings/members"]}>
                <LangContext.Provider value={{ lang: "en", setLang: () => {} }}>
                    <ThemeContext.Provider value={{ theme: "light", toggleTheme: () => {} }}>
                        <CurrentUserContext.Provider
                            value={{
                                currentUser: {
                                    id: 1,
                                    roles: ["administrator"],
                                    clubIds: [],
                                    managedTeamIds: [],
                                },
                                setCurrentUser: () => {},
                                loadingUser: false,
                                reloadCurrentUser: vi.fn(),
                            }}
                        >
                            <AddManagerButton
                                teamId={77}
                                team={{ id: 77, clubId: 1 }}
                                onAdded={vi.fn()}
                            />
                        </CurrentUserContext.Provider>
                    </ThemeContext.Provider>
                </LangContext.Provider>
            </MemoryRouter>,
        );

        await user.click(screen.getByRole("button", { name: "Beheerder toevoegen" }));
        expect(screen.getByPlaceholderText("Naam, e-mail of ID…")).toBeInTheDocument();
    });

    // Verifies disputed score submission updates ratings and clears the queue.
    test("disputed match adjudication updates the ladder ratings", async () => {
        const user = userEvent.setup();

        disputedHookState.matches = [
            {
                id: 55,
                team1Id: 1,
                team2Id: 2,
                team1Name: "Topspin Tigers",
                team2Name: "Court Kings",
                ladderName: "Singles Ladder",
                ladderId: 10,
                ruleSetName: "Standard Ladder",
                scoreSubmissions: [
                    {
                        id: 101,
                        submittedByRole: "team1_side",
                        scoreTeam1: 2,
                        scoreTeam2: 1,
                        submittedAt: "2026-05-14T10:00:00Z",
                    },
                    {
                        id: 102,
                        submittedByRole: "team2_side",
                        scoreTeam1: 1,
                        scoreTeam2: 2,
                        submittedAt: "2026-05-14T10:05:00Z",
                    },
                ],
                ruleSnapshot: {
                    rules: [
                        { id: 1, name: "Best of 3 sets" },
                        { id: 2, name: "Golden Point" },
                    ],
                },
            },
        ];
        disputedHookState.total = 1;

        renderWithLang(
            <Routes>
                <Route path="/clubs/:clubId/settings/disputed" element={<ClubDisputedMatchesPage />} />
            </Routes>,
            { route: "/clubs/1/settings/disputed" },
        );

        expect(await screen.findByText("Dispute queue")).toBeInTheDocument();
        await user.click(screen.getByRole("listitem"));

        const scoreInputs = screen.getAllByRole("spinbutton");
        await user.clear(scoreInputs[0]);
        await user.type(scoreInputs[0], "2");
        await user.clear(scoreInputs[1]);
        await user.type(scoreInputs[1], "1");

        await user.click(screen.getByRole("button", { name: "Submit decisive score" }));

        await waitFor(() => {
            expect(global.fetch).toHaveBeenCalledWith(
                "/api/matches/55/score",
                expect.objectContaining({ method: "POST" }),
            );
        });

        const scoreCall = getFetchCall("/api/matches/55/score", "POST");
        expect(JSON.parse(scoreCall[1].body)).toEqual({
            score_team1: 2,
            score_team2: 1,
        });
        expect(disputedHookState.reload).toHaveBeenCalled();

        ladderHookState.ladder = {
            id: 10,
            name: "Singles Ladder",
            sport_type: "Padel",
            rating_function: "Elo",
            ruleset: {
                name: "Standard Ladder",
                matchFormat: "best_of_3",
                thirdSetFormat: "super_tiebreak",
                deuceRule: "advantage",
                gameFormat: "doubles",
            },
        };

        renderWithLang(
            <Routes>
                <Route path="/clubs/:clubId/ladders/:ladderId" element={<Ladder />} />
            </Routes>,
            { route: "/clubs/1/ladders/10" },
        );

        expect(await screen.findByRole("heading", { name: "Singles Ladder" })).toBeInTheDocument();
        expect(screen.getByText("1020")).toBeInTheDocument();
        expect(screen.getByText("980")).toBeInTheDocument();
        expect(screen.getByText("Elo")).toBeInTheDocument();
    });

    // Verifies a timed ruleset can be created from the club settings tab.
    test("rules tab can create a new timed ruleset", async () => {
        const user = userEvent.setup();

        renderWithLang(<ClubMatchRules clubId={1} texts={clubSettingsTextState} />);

        expect(await screen.findByText("Bestaande regelsets")).toBeInTheDocument();
        expect(screen.getByText("Standard Ladder")).toBeInTheDocument();

        await user.type(screen.getByPlaceholderText("Naam van de regelset"), "Fast Padel");
        await user.type(screen.getByPlaceholderText("Omschrijving (optioneel)"), "Shorter matches for training");

        await user.selectOptions(screen.getByDisplayValue("Best of 3 sets"), "timed");
        await user.clear(screen.getByPlaceholderText("Speelduur in minuten (bijv. 60)"));
        await user.type(screen.getByPlaceholderText("Speelduur in minuten (bijv. 60)"), "45");

        await user.click(screen.getByRole("button", { name: "Regelset opslaan" }));

        await waitFor(() => {
            expect(global.fetch).toHaveBeenCalledWith(
                "/api/match-rule-sets",
                expect.objectContaining({ method: "POST" }),
            );
        });

        const createCall = getFetchCall("/api/match-rule-sets", "POST");
        expect(JSON.parse(createCall[1].body)).toEqual(
            expect.objectContaining({
                name: "Fast Padel",
                description: "Shorter matches for training",
                matchFormat: "timed",
                timedDurationMinutes: 45,
                clubId: 1,
            }),
        );

        expect(screen.getByText("Fast Padel")).toBeInTheDocument();
        expect(screen.getByText("Op tijd spelen – 45 min · Klassiek (Voordeel) · Dubbelspel (2v2)")).toBeInTheDocument();
    });

    // Verifies the ladder modal shows the frozen rule snapshot for a ladder.
    test("ladder ruleset modal shows the frozen ruleset details", async () => {
        const user = userEvent.setup();

        ladderHookState.ladder = {
            id: 10,
            name: "Singles Ladder",
            sport_type: "Padel",
            rating_function: "Elo",
            ruleset: {
                name: "Weekend Rules",
                description: "Used for weekend play only",
                matchFormat: "best_of_3",
                thirdSetFormat: "super_tiebreak",
                deuceRule: "golden_point",
                gameFormat: "singles",
            },
        };
        ladderHookState.players = [
            { id: 1, name: "Topspin Tigers", rating: 1020 },
            { id: 2, name: "Court Kings", rating: 980 },
        ];

        renderWithLang(
            <Routes>
                <Route path="/clubs/:clubId/ladders/:ladderId" element={<Ladder />} />
            </Routes>,
            { route: "/clubs/1/ladders/10" },
        );

        expect(await screen.findByText("Singles Ladder")).toBeInTheDocument();
        await user.click(screen.getByRole("button", { name: "Weekend Rules" }));

        expect(await screen.findByRole("heading", { name: "Weekend Rules" })).toBeInTheDocument();
        expect(screen.getByText("Used for weekend play only")).toBeInTheDocument();
        expect(screen.getByText("Wedstrijdformaat")).toBeInTheDocument();
        expect(screen.getByText("Best of 3 sets")).toBeInTheDocument();
        expect(screen.getByText("Derde set")).toBeInTheDocument();
        expect(screen.getByText("Super Tiebreak (tot 10 punten)")).toBeInTheDocument();
        expect(screen.getByText("40-40 (Deuce)")).toBeInTheDocument();
        expect(screen.getByText("Golden Point (No-Ad)")).toBeInTheDocument();
        expect(screen.getByText("Spelvorm")).toBeInTheDocument();
        expect(screen.getByText("Enkelspel (1v1)")).toBeInTheDocument();
    });

    // Verifies non-racket clubs do not show a ruleset field in the ladder create form.
    test("ladder create form hides ruleset selection for basketball", async () => {
        const user = userEvent.setup();

        renderWithLang(
            <ClubLadders
                ladders={[]}
                onCreate={vi.fn()}
                ratingFunctions={[{ id: 1, name: "Elo" }]}
                ruleSets={[{ id: 1, name: "Standard Ladder" }]}
                eligibleTeams={[]}
                onAddTeam={vi.fn()}
                supportsRuleSets={false}
                texts={{
                    choose_sport_type: "Choose a sport type",
                    choose_rule_set: "Choose a ruleset",
                    choose_rating_function: "Choose rating",
                    create_ladder: "Create ladder",
                    ladder_create_title: "Create ladder",
                }}
            />,
        );

        const sportSelect = screen.getAllByRole("combobox")[0];
        await user.selectOptions(sportSelect, "2");

        expect(screen.queryByText("Choose a ruleset")).not.toBeInTheDocument();
    });

    // Verifies racket clubs still show a ruleset field in the ladder create form.
    test("ladder create form shows ruleset selection for tennis", async () => {
        renderWithLang(
            <ClubLadders
                ladders={[]}
                onCreate={vi.fn()}
                ratingFunctions={[{ id: 1, name: "Elo" }]}
                ruleSets={[{ id: 1, name: "Standard Ladder" }]}
                eligibleTeams={[]}
                onAddTeam={vi.fn()}
                supportsRuleSets={true}
                texts={{
                    choose_sport_type: "Choose a sport type",
                    choose_rule_set: "Choose a ruleset",
                    choose_rating_function: "Choose rating",
                    create_ladder: "Create ladder",
                    ladder_create_title: "Create ladder",
                }}
            />,
        );

        expect(screen.getByText("Choose a ruleset")).toBeInTheDocument();
    });

    // Verifies ladder settings expose remove-team and delete-ladder controls.
    test("ladder management controls remove teams and delete ladders", async () => {
        const user = userEvent.setup();
        const onRemoveTeam = vi.fn().mockResolvedValue({ cancelledMatches: 1 });
        const onDeleteLadder = vi.fn().mockResolvedValue({});
        const confirmSpy = vi.spyOn(window, "confirm").mockReturnValue(true);

        renderWithLang(
            <ClubLadders
                ladders={[{ id: 10, name: "Premier Ladder", description: "Top division", ruleset_id: 1 }]}
                onCreate={vi.fn()}
                ratingFunctions={[{ id: 1, name: "Elo" }]}
                ruleSets={[{ id: 1, name: "Standard Ladder" }]}
                eligibleTeams={[
                    {
                        id: 44,
                        name: "NetRank Aces",
                        membershipStatus: "club",
                        ladderIds: [10],
                        playerCount: 2,
                        managerCount: 1,
                        players: [],
                        managers: [],
                    },
                ]}
                onAddTeam={vi.fn()}
                onRemoveTeam={onRemoveTeam}
                onDeleteLadder={onDeleteLadder}
                supportsRuleSets={true}
                texts={{
                    ladders_title: "Ladders",
                    delete_ladder: "Delete ladder",
                    remove_from_ladder: "Remove",
                    teams_in_ladder: "Teams in ladder",
                    team_players_label: "Players",
                    team_managers_label: "Managers",
                }}
            />,
        );

        expect(screen.getByText("Teams in ladder: 1")).toBeInTheDocument();
        expect(screen.getByText("Rule set: Standard Ladder")).toBeInTheDocument();
        expect(screen.getByText("NetRank Aces", { selector: "p" })).toBeInTheDocument();

        await user.click(screen.getByRole("button", { name: "Remove" }));
        expect(onRemoveTeam).toHaveBeenCalledWith(10, 44);

        await user.click(screen.getByRole("button", { name: "Delete ladder" }));
        expect(onDeleteLadder).toHaveBeenCalledWith(10);

        confirmSpy.mockRestore();
    });

    // Verifies oversized independent teams also show the warning before the invite is sent.
    test("oversized independent team shows warning before invitation", async () => {
        const user = userEvent.setup();
        const onAddTeam = vi.fn()
            .mockResolvedValueOnce({
                action: "invitation_sent",
                invitation: { id: 77 },
            });

        renderWithLang(
            <ClubLadders
                ladders={[{ id: 10, name: "Padel Ladder", ruleset_id: 1, sport_type_id: 2 }]}
                onCreate={vi.fn()}
                ratingFunctions={[{ id: 1, name: "Elo" }]}
                ruleSets={[{ id: 1, name: "Standard Padel", gameFormat: "doubles" }]}
                eligibleTeams={[
                    {
                        id: 77,
                        name: "Nomads United",
                        membershipStatus: "independent",
                        requiresInvite: true,
                        ladderIds: [],
                        playerCount: 3,
                        managerCount: 1,
                        players: [{ name: "A" }, { name: "B" }, { name: "C" }],
                        managers: [{ name: "Coach" }],
                    },
                ]}
                onAddTeam={onAddTeam}
                supportsRuleSets={true}
                texts={{
                    add_team_title: "Team toevoegen aan ladder",
                    add_team_subtitle: "Select a ladder and a team to link them.",
                    ladder_team_size_hint: "This ladder expects teams of up to 2 players.",
                    team_too_large_for_ladder: "This team has 3 players, but the selected ladder expects teams of at most 2.",
                    team_group_hint: "Club teams can be added directly. Independent teams need an invite first. Ladder team size limits are shown for the selected ladder.",
                    select_ladder: "Selecteer een ladder",
                    select_team: "Selecteer een team",
                    teams_from_your_club: "Teams from your club",
                    independent_teams: "Independent teams",
                    team_size_warning_title: "Team size warning",
                    team_size_warning_body: "This team is larger than the selected ladder expects. You can still add it, or create a new team instead.",
                    create_new_team: "Create new team",
                    invite_team: "Invite team",
                }}
            />,
        );

        const selects = screen.getAllByRole("combobox");
        await user.selectOptions(selects[3], "10");
        await user.selectOptions(selects[4], "77");

        expect(screen.getByText("This team has 3 players, but the selected ladder expects teams of at most 2.")).toBeInTheDocument();

        await user.click(screen.getByRole("button", { name: "Invite team" }));
        expect(onAddTeam).toHaveBeenCalledTimes(1);
        expect(onAddTeam).toHaveBeenCalledWith(10, 77, true, false);
        expect(await screen.findByText("Invitation sent to the team manager.")).toBeInTheDocument();
    });

    // Verifies sport mismatches warn first but still allow adding the team.
    test("sport mismatch warns before adding the team", async () => {
        const user = userEvent.setup();
        const onAddTeam = vi.fn().mockResolvedValueOnce({
            action: "added",
            team: { id: 44, name: "Padel Club Team", sportTypeId: 1, sportName: "Tennis" },
        });

        renderWithLang(
            <ClubLadders
                ladders={[{ id: 10, name: "Tennis Ladder", ruleset_id: 1, sport_type_id: 1 }]}
                onCreate={vi.fn()}
                ratingFunctions={[{ id: 1, name: "Elo" }]}
                ruleSets={[{ id: 1, name: "Standard Tennis", gameFormat: "doubles" }]}
                eligibleTeams={[
                    {
                        id: 44,
                        name: "Padel Club Team",
                        membershipStatus: "club",
                        ladderIds: [],
                        playerCount: 2,
                        managerCount: 1,
                        sportTypeId: 2,
                        sportName: "Padel",
                        players: [{ name: "A" }, { name: "B" }],
                        managers: [{ name: "Coach" }],
                    },
                ]}
                onAddTeam={onAddTeam}
                supportsRuleSets={true}
                texts={{
                    add_team_title: "Team toevoegen aan ladder",
                    add_team_subtitle: "Select a ladder and a team to link them.",
                    ladder_team_size_hint: "This ladder expects teams of up to 2 players.",
                    team_group_hint: "Club teams can be added directly. Independent teams need an invite first. Ladder team size limits are shown for the selected ladder.",
                    select_ladder: "Selecteer een ladder",
                    select_team: "Selecteer een team",
                    teams_from_your_club: "Teams from your club",
                    independent_teams: "Independent teams",
                    team_sport_mismatch_warning_title: "Team sport warning",
                    team_sport_mismatch_warning_body: "This team is a different sport, but this ladder expects another sport. Accepting will change the team's sport type to match the ladder.",
                    team_sport_mismatch_warning_team: "Current sport",
                }}
            />,
        );

        const selects = screen.getAllByRole("combobox");
        await user.selectOptions(selects[3], "10");
        await user.selectOptions(selects[4], "44");

        expect(screen.getByText("This team is a different sport, but this ladder expects another sport. Accepting will change the team's sport type to match the ladder.")).toBeInTheDocument();

        await user.click(screen.getByRole("button", { name: "Team toevoegen" }));
        await waitFor(() => expect(onAddTeam).toHaveBeenCalledTimes(1));
        expect(onAddTeam).toHaveBeenCalledWith(10, 44, false, true);
        expect(await screen.findByText("Team added to ladder.")).toBeInTheDocument();
    });

    // Verifies ladder warnings still allow club managers to continue after confirmation.
    test("ladder warning allows oversized team add after confirmation", async () => {
        const user = userEvent.setup();
        const onAddTeam = vi.fn()
            .mockResolvedValueOnce({
                action: "added",
                team: { id: 44, name: "NetRank Aces" },
            });

        renderWithLang(
            <ClubLadders
                ladders={[{ id: 10, name: "Singles Ladder", sport_type_id: 1 }]}
                onCreate={vi.fn()}
                ratingFunctions={[{ id: 1, name: "Elo" }]}
                ruleSets={[{ id: 1, name: "Standard Ladder" }]}
                eligibleTeams={[
                    {
                        id: 44,
                        name: "NetRank Aces",
                        membershipStatus: "club",
                        ladderIds: [],
                        playerCount: 2,
                        managerCount: 1,
                        players: [{ name: "Alice" }, { name: "Bob" }],
                        managers: [{ name: "Coach" }],
                    },
                ]}
                onAddTeam={onAddTeam}
                supportsRuleSets={true}
                texts={{
                    add_team_title: "Team toevoegen aan ladder",
                    add_team_subtitle: "Select a ladder and a team to link them.",
                    ladder_team_size_hint: "This ladder expects teams of up to 1 player.",
                    team_too_large_for_ladder: "This team has 2 players, but the selected ladder expects teams of at most 1.",
                    team_group_hint: "Club teams can be added directly. Independent teams need an invite first. Ladder team size limits are shown for the selected ladder.",
                    select_ladder: "Selecteer een ladder",
                    select_team: "Selecteer een team",
                    teams_from_your_club: "Teams from your club",
                    independent_teams: "Independent teams",
                    team_size_warning_title: "Team size warning",
                    team_size_warning_body: "This team is larger than the selected ladder expects. You can still add it, or create a new team instead.",
                }}
            />,
        );

        const selects = screen.getAllByRole("combobox");
        await user.selectOptions(selects[3], "10");
        await user.selectOptions(selects[4], "44");

        expect(screen.getByText("This ladder expects teams of up to 1 player.")).toBeInTheDocument();
        expect(screen.getByText("This team has 2 players, but the selected ladder expects teams of at most 1.")).toBeInTheDocument();
        expect(screen.getByRole("button", { name: "Create a team first" })).toBeInTheDocument();
        expect(screen.getByRole("button", { name: "Team toevoegen" })).not.toBeDisabled();

        await user.click(screen.getByRole("button", { name: "Team toevoegen" }));
        await waitFor(() => expect(onAddTeam).toHaveBeenCalledTimes(1));
        expect(onAddTeam).toHaveBeenCalledWith(10, 44, true, false);
        expect(await screen.findByText("Team added to ladder.")).toBeInTheDocument();
    });

    // Verifies non-racket clubs do not show the rules tab in settings.
    test("settings sidebar hides rules tab for basketball", async () => {
        renderWithLang(
            <ClubSidebar
                activeTab="general"
                onTabChange={vi.fn()}
                texts={clubSettingsTextState}
                supportsRuleSets={false}
            />,
        );

        expect(screen.queryByRole("button", { name: "Match rules" })).not.toBeInTheDocument();
    });
});
