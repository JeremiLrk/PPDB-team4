import "@testing-library/jest-dom/vitest";
import React from "react";
import { beforeEach, describe, expect, test, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";

import { LangContext } from "../src/context/useLangContext.jsx";
import ClubDisputedMatchesPage from "../src/pages/ClubDisputedMatchesPage.jsx";
import ClubMatchRules from "../src/components/club_settings/ClubMatchRules.jsx";
import Ladder from "../src/pages/Ladder.jsx";

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

describe("Disputed matches and rulesets", () => {
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
});
