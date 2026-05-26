import "@testing-library/jest-dom/vitest";
import React from "react";
import { describe, expect, test, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

import CreateMatchButton from "../src/components/matches/CreateMatchButton.jsx";
import CurrentUserContext from "../src/context/useCurrentUserContext.jsx";
import { LangContext } from "../src/context/useLangContext.jsx";
import { ThemeContext } from "../src/context/useThemeContext.jsx";

vi.mock("../src/hooks/matches/useCreateMatch.js", () => ({
    useCreateMatch: () => ({
        isOpen: true,
        isLoading: false,
        isSuccess: false,
        error: "",
        openPanel: vi.fn(),
        closePanel: vi.fn(),
        step: 2,
        nextStep: vi.fn(),
        prevStep: vi.fn(),
        canNext: true,
        selectedTeamId: "11",
        setSelectedTeamId: vi.fn(),
        ladders: [{ id: 1, name: "Premier Ladder" }],
        laddersLoading: false,
        laddersError: "",
        selectedLadderId: "1",
        setSelectedLadderId: vi.fn(),
        peers: [
            { id: 22, name: "Rally Rockets", clubName: "NetRank Club", rank: 1, rating: 1020 },
        ],
        peersLoading: false,
        peersError: "",
        selectedPeerId: "22",
        setSelectedPeerId: vi.fn(),
        submit: vi.fn(),
    }),
}));

vi.mock("../src/hooks/common/usePageTexts.js", () => ({
    usePageTexts: () => ({
        create_match_title: "Create Match",
        create_match_btn: "New Match",
        create_match_submit: "Send Proposal",
        create_match_aria: "Create a new match proposal",
        create_match_pick_opponent: "Choose an opponent:",
        create_match_selected_btn: "Selected",
        create_match_select_btn: "Select",
        create_match_your_team: "Your Team *",
        create_match_ladder: "Ladder *",
        create_match_select_team: "-- Select a team --",
        create_match_select_ladder: "-- Select a ladder --",
        create_match_loading_ladders: "Loading ladders...",
        create_match_loading_opponents: "Loading opponents...",
        create_match_no_ladders: "This team is not registered in any ladder.",
        create_match_no_opponents: "No other teams in this ladder yet.",
        match_created: "Match proposal sent!",
    }),
}));

describe("CreateMatchButton light theme", () => {
    test("renders opponent names with readable light-mode text", () => {
        render(
            <MemoryRouter>
                <ThemeContext.Provider value={{ theme: "light", toggleTheme: () => {} }}>
                    <LangContext.Provider value={{ lang: "en", setLang: () => {} }}>
                        <CurrentUserContext.Provider
                            value={{
                                currentUser: {
                                    id: 7,
                                    roles: ["administrator"],
                                    role: "administrator",
                                },
                                setCurrentUser: vi.fn(),
                                loadingUser: false,
                            }}
                        >
                            <CreateMatchButton
                                theme="light"
                                managedTeams={[{ id: 11, name: "NetRank Aces", clubId: 1, clubName: "NetRank Club", sportTypeId: 1 }]}
                                onCreated={vi.fn()}
                            />
                        </CurrentUserContext.Provider>
                    </LangContext.Provider>
                </ThemeContext.Provider>
            </MemoryRouter>,
        );

        expect(screen.getByText("Rally Rockets")).toHaveStyle({
            color: "#0f172a",
        });
        expect(screen.getByText("NetRank Club | #1 | 1020 pts")).toHaveStyle({
            color: "#475569",
        });
    });
});
