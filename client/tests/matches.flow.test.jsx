import "@testing-library/jest-dom/vitest";
import React from "react";
import { beforeEach, describe, expect, test, vi } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";

import CurrentUserContext from "../src/context/useCurrentUserContext.jsx";
import { LangContext } from "../src/context/useLangContext.jsx";
import MatchProposalsTab from "../src/components/matches/MatchProposalsTab.jsx";
import ClubDisputedMatchesPage from "../src/pages/ClubDisputedMatchesPage.jsx";

const matchProposalsState = vi.hoisted(() => ({
    proposals: [],
    load: vi.fn(),
    setProposalStatus: vi.fn(),
}));

const teamsState = vi.hoisted(() => ({
    teams: [],
    loading: false,
}));

const disputedState = vi.hoisted(() => ({
    matches: [],
    total: 0,
    loading: false,
    error: null,
    forbidden: false,
    reload: vi.fn(),
}));

const clubSettingsState = vi.hoisted(() => ({
    loading: false,
}));

const pageTextsState = vi.hoisted(() => ({
    matches: {
        title: "Weekly Match Proposals",
        refresh: "Refresh",
        loading: "Match proposals loading...",
        empty: "No match proposals yet.",
        retry: "Retry",
        accept: "Accept",
        reject: "Reject",
        cancel: "Cancel",
        reset_pending: "Set back to pending",
        report_score: "Add Score",
        adjudicate_title: "Submit decisive score",
        confirm: "Submit",
        score_finalized: "Result confirmed. Elo ratings updated.",
        score_disputed: "Scores do not match. A club manager will decide the decisive score.",
        score_waiting: "Score submitted. Waiting for the other team.",
        waiting_for_other_player: "Waiting for other player",
        managed_matches: "Managed matches",
        managed_matches_subtitle: "Matches for teams and clubs you manage.",
        player_matches: "Player matches",
        player_matches_subtitle: "Matches that involve teams you play on.",
        no_managed_matches: "No managed match proposals yet.",
        no_player_matches: "No player match proposals yet.",
        team_1: "Team 1",
        team_2: "Team 2",
        no_contacts: "No contact info",
        club: "club",
        proposed_date: "Proposed date",
        weather_loading: "Weather for {city} on {date} loading...",
        weather_available: "Weather for {city} on {date}: {temp}°C{description}",
        weather_unavailable: "Weather for {city} on {date} unavailable",
    },
    dashboard: {
        status_accepted: "Accepted",
        status_rejected: "Rejected",
        status_cancelled: "Cancelled",
        status_played: "Played",
        status_finished: "Finished",
        status_pending: "Pending",
        score_finalized: "Result confirmed. Elo ratings updated.",
        score_disputed: "Scores do not match. A club manager will decide the decisive score.",
        score_waiting: "Score submitted. Waiting for the other team.",
    },
    club_settings: {
        sidebar_title: "Settings",
        tab_general: "General info",
        tab_ladders: "Ladders",
        tab_members: "Members",
        tab_rules: "Match rules",
        tab_owners: "Owners",
        tab_home: "Go to club home",
        tab_disputed: "Disputed matches",
        loading: "Loading...",
        disputed_description: "Matches where both teams submitted conflicting scores.",
        disputed_queue_title: "Dispute queue",
        no_disputed: "No disputed matches at this time.",
        retry: "Retry",
        select_match_prompt: "Select a disputed match from the list to review and adjudicate it.",
        submitted_scores: "Submitted scores",
        rules_snapshot_title: "Rules in effect",
        adjudicate_title: "Submit decisive score",
        submit_decisive_score: "Submit decisive score",
        submitting: "Submitting...",
        ladder_admin_label: "Ladder admin",
        no_ladder: "No ladder",
        no_ruleset: "None",
        back: "Back to settings",
    },
}));

vi.mock("../src/hooks/useMatchProposals.js", () => ({
    useMatchProposals: () => ({
        proposals: matchProposalsState.proposals,
        loading: false,
        error: "",
        submitting: false,
        load: matchProposalsState.load,
        setProposalStatus: matchProposalsState.setProposalStatus,
    }),
}));

vi.mock("../src/hooks/teams/useTeams.js", () => ({
    useTeams: () => ({
        teams: teamsState.teams,
        loading: teamsState.loading,
    }),
}));

vi.mock("../src/hooks/useWeather.js", () => ({
    useWeather: () => ({ weather: null, loading: false }),
}));

vi.mock("../src/hooks/useClubSettings.js", () => ({
    useClubSettings: () => clubSettingsState,
}));

vi.mock("../src/hooks/matches/useDisputedMatches.js", () => ({
    useDisputedMatches: () => disputedState,
}));

vi.mock("../src/hooks/common/usePageTexts.js", () => ({
    usePageTexts: (page) => pageTextsState[page] || {},
}));

vi.mock("../src/components/matches/CreateMatchButton.jsx", () => ({
    default: () => React.createElement("button", { type: "button" }, "Create match"),
}));

vi.mock("../src/components/club_settings/ClubSidebar.jsx", () => ({
    default: () => React.createElement("aside", { "data-testid": "club-sidebar" }),
}));

beforeEach(() => {
    matchProposalsState.proposals = [];
    matchProposalsState.load.mockReset();
    matchProposalsState.setProposalStatus.mockReset();

    teamsState.teams = [{ id: 11, name: "NetRank Aces" }];
    teamsState.loading = false;

    disputedState.matches = [];
    disputedState.total = 0;
    disputedState.loading = false;
    disputedState.error = null;
    disputedState.forbidden = false;
    disputedState.reload.mockReset();

    clubSettingsState.loading = false;

    global.fetch = vi.fn();
});

function renderWithContexts(ui, { lang = "en", currentUser = null, route = "/" } = {}) {
    return render(
        <MemoryRouter initialEntries={[route]}>
            <LangContext.Provider value={{ lang, setLang: () => {} }}>
                <CurrentUserContext.Provider
                    value={{
                        currentUser,
                        setCurrentUser: () => {},
                        loadingUser: false,
                    }}
                >
                    {ui}
                </CurrentUserContext.Provider>
            </LangContext.Provider>
        </MemoryRouter>,
    );
}

describe("Match frontend flows", () => {
    test("weekly proposals tab can accept a proposal and submit a score", async () => {
        const user = userEvent.setup();

        matchProposalsState.proposals = [
            {
                id: 1,
                proposedByUserId: 9,
                team1Id: 11,
                team2Id: 12,
                team1Name: "NetRank Aces",
                team2Name: "NetRank Juniors",
                team1ClubId: 1,
                team2ClubId: 1,
                team1ClubName: "NetRank Club",
                team2ClubName: "NetRank Club",
                team1ClubCity: "Antwerp",
                team2ClubCity: "Antwerp",
                team1Contacts: [],
                team2Contacts: [],
                status: "pending",
                scoreStatus: "not_submitted",
                scoreSubmissions: [],
                proposedStartAt: "2026-05-15T18:00:00Z",
                proposedEndAt: "2026-05-15T19:00:00Z",
            },
            {
                id: 2,
                proposedByUserId: 9,
                team1Id: 11,
                team2Id: 13,
                team1Name: "NetRank Aces",
                team2Name: "NetRank Challengers",
                team1ClubId: 1,
                team2ClubId: 1,
                team1ClubName: "NetRank Club",
                team2ClubName: "NetRank Club",
                team1ClubCity: "Antwerp",
                team2ClubCity: "Antwerp",
                team1Contacts: [],
                team2Contacts: [],
                status: "accepted",
                scoreStatus: "not_submitted",
                scoreSubmissions: [
                    { id: 5, submittedBy: 8, submittedByRole: "team2_side", scoreTeam1: 2, scoreTeam2: 1 },
                ],
                proposedStartAt: "2026-05-16T18:00:00Z",
                proposedEndAt: "2026-05-16T19:00:00Z",
            },
            {
                id: 3,
                proposedByUserId: 9,
                acceptedByUserId: 7,
                acceptanceStatus: "waiting_for_other",
                team1Id: 11,
                team2Id: 14,
                team1Name: "NetRank Aces",
                team2Name: "NetRank Masters",
                team1ClubId: 1,
                team2ClubId: 1,
                team1ClubName: "NetRank Club",
                team2ClubName: "NetRank Club",
                team1ClubCity: "Antwerp",
                team2ClubCity: "Antwerp",
                team1Contacts: [],
                team2Contacts: [],
                status: "pending",
                scoreStatus: "not_submitted",
                scoreSubmissions: [],
                proposedStartAt: "2026-05-17T18:00:00Z",
                proposedEndAt: "2026-05-17T19:00:00Z",
            },
            {
                id: 4,
                proposedByUserId: 9,
                team1Id: 11,
                team2Id: 15,
                team1Name: "NetRank Aces",
                team2Name: "NetRank Resolved",
                team1ClubId: 1,
                team2ClubId: 1,
                team1ClubName: "NetRank Club",
                team2ClubName: "NetRank Club",
                team1ClubCity: "Antwerp",
                team2ClubCity: "Antwerp",
                team1Contacts: [],
                team2Contacts: [],
                status: "played",
                scoreStatus: "resolved",
                scoreSubmissions: [],
                proposedStartAt: "2026-05-18T18:00:00Z",
                proposedEndAt: "2026-05-18T19:00:00Z",
            },
            {
                id: 5,
                proposedByUserId: 9,
                team1Id: 11,
                team2Id: 16,
                team1Name: "NetRank Aces",
                team2Name: "NetRank Disputed",
                team1ClubId: 1,
                team2ClubId: 1,
                team1ClubName: "NetRank Club",
                team2ClubName: "NetRank Club",
                team1ClubCity: "Antwerp",
                team2ClubCity: "Antwerp",
                team1Contacts: [],
                team2Contacts: [],
                status: "accepted",
                scoreStatus: "disputed",
                scoreSubmissions: [
                    { id: 6, submittedBy: 7, submittedByRole: "team1_side", scoreTeam1: 2, scoreTeam2: 1 },
                    { id: 7, submittedBy: 8, submittedByRole: "team2_side", scoreTeam1: 1, scoreTeam2: 2 },
                ],
                proposedStartAt: "2026-05-19T18:00:00Z",
                proposedEndAt: "2026-05-19T19:00:00Z",
            },
        ];
        matchProposalsState.load.mockResolvedValue(undefined);

        renderWithContexts(<MatchProposalsTab />, {
            currentUser: {
                id: 7,
                role: "team_manager",
                managedTeamIds: [11],
                clubIds: [1],
                playerTeamIds: [],
            },
        });

        expect(await screen.findByRole("button", { name: "Accept" })).toBeInTheDocument();
        expect(screen.getByRole("button", { name: "Reject" })).toBeInTheDocument();
        expect(screen.getByRole("button", { name: "Add Score" })).toBeInTheDocument();
        expect(screen.getAllByText(/club:\s*NetRank Club/i).length).toBeGreaterThan(0);
        expect(screen.getByText("Waiting for other player")).toBeInTheDocument();
        expect(screen.getByText("Finished")).toBeInTheDocument();
        expect(screen.getByText("Result confirmed. Elo ratings updated.")).toBeInTheDocument();
        expect(screen.getByText("Scores do not match. A club manager will decide the decisive score.")).toBeInTheDocument();

        await user.click(screen.getByRole("button", { name: "Add Score" }));
        const scoreForm = screen.getByText("Submit decisive score").closest("form");
        expect(scoreForm).toBeInTheDocument();

        const inputs = screen.getAllByRole("spinbutton");
        await user.type(inputs[0], "2");
        await user.type(inputs[1], "1");

        global.fetch.mockResolvedValue({
            ok: true,
            status: 201,
            json: async () => ({
                finalized: false,
                scoreStatus: "not_submitted",
            }),
        });

        await user.click(within(scoreForm).getByRole("button", { name: "Submit" }));

        expect(global.fetch).toHaveBeenCalledWith(
            "/api/matches/2/score",
            expect.objectContaining({
                method: "POST",
                credentials: "include",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ score_team1: 2, score_team2: 1 }),
            }),
        );
        expect(matchProposalsState.load).toHaveBeenCalled();
        expect(screen.queryByText("Submit decisive score")).not.toBeInTheDocument();
    });

    test("disputed matches page can adjudicate a disputed match and show confirmation", async () => {
        const user = userEvent.setup();

        disputedState.matches = [
            {
                id: 44,
                team1Id: 11,
                team2Id: 12,
                team1Name: "NetRank Aces",
                team2Name: "NetRank Juniors",
                ladderName: "Singles Ladder",
                weekStartDate: "2026-05-12",
                scoreSubmissions: [
                    { id: 1, submittedByRole: "team1_side", scoreTeam1: 2, scoreTeam2: 1 },
                    { id: 2, submittedByRole: "team2_side", scoreTeam1: 1, scoreTeam2: 2 },
                ],
            },
        ];
        disputedState.total = 1;

        global.fetch.mockResolvedValue({
            ok: true,
            status: 201,
            json: async () => ({
                finalized: true,
                resolvedScore: { scoreTeam1: 2, scoreTeam2: 1 },
            }),
        });

        render(
            <MemoryRouter initialEntries={["/clubs/1/settings/disputed"]}>
                <Routes>
                    <Route
                        path="/clubs/:clubId/settings/disputed"
                        element={
                            <LangContext.Provider value={{ lang: "en", setLang: () => {} }}>
                                <ClubDisputedMatchesPage />
                            </LangContext.Provider>
                        }
                    />
                </Routes>
            </MemoryRouter>,
        );

        expect(await screen.findByText("Dispute queue")).toBeInTheDocument();
        await user.click(screen.getByText("Singles Ladder"));

        const inputs = screen.getAllByRole("spinbutton");
        await user.type(inputs[0], "2");
        await user.type(inputs[1], "1");

        await user.click(screen.getByRole("button", { name: "Submit decisive score" }));

        expect(global.fetch).toHaveBeenCalledWith(
            "/api/matches/44/score",
            expect.objectContaining({
                method: "POST",
                credentials: "include",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ score_team1: 2, score_team2: 1 }),
            }),
        );
        expect(disputedState.reload).toHaveBeenCalled();
        expect(await screen.findByText("Select a disputed match from the list to review and adjudicate it.")).toBeInTheDocument();
    });
});
