import "@testing-library/jest-dom/vitest";
import React from "react";
import { beforeEach, afterEach, describe, expect, test, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";

import ClubHome from "../src/pages/ClubHome.jsx";
import { ThemeContext } from "../src/context/useThemeContext.jsx";

const originalFetch = global.fetch;

vi.mock("../src/context/useLangContext.jsx", () => ({
    useLangContext: () => ({ lang: "en" }),
}));

vi.mock("../src/context/useCurrentUserContext.jsx", () => ({
    useCurrentUserContext: () => ({ currentUser: null, loadingUser: false }),
}));

vi.mock("../src/hooks/common/usePageTexts.js", () => ({
    usePageTexts: (page) => {
        if (page === "ladder") {
            return { ladder: "Ladders", join_ladder: "Join the ladder" };
        }
        if (page === "club_home") {
            return {
                upcoming_title: "Upcoming matches",
                ladder_label: "Ladder",
                no_upcoming_matches: "No upcoming matches scheduled.",
            };
        }
        return {};
    },
}));

vi.mock("../src/hooks/useClubHomeSummary", () => ({
    useClubHomeSummary: () => ({
        summary: {
            club: {
                id: 1,
                name: "NetRank Club",
                sport: "Tennis",
                description: "Club description",
            },
            ladders: [],
            performers: [],
            upcomingMatches: [
                {
                    id: 101,
                    team1Name: "NetRank Aces",
                    team2Name: "Rally Rockets",
                    ladderName: "Premier Ladder",
                },
            ],
            latestResults: [],
        },
        loading: false,
        error: null,
    }),
}));

vi.mock("../src/hooks/useMatchPercentages.js", () => ({
    fetchMatchPercentages: vi.fn(async () => ({
        team1WinPercentage: 52,
        team2WinPercentage: 48,
    })),
}));

describe("ClubHome light theme", () => {
    beforeEach(() => {
        document.documentElement.classList.add("light");
        global.fetch = vi.fn(async (input) => {
            if (input === "/api/clubs/1/is_manager") {
                return {
                    ok: true,
                    json: async () => ({ is_manager: false }),
                };
            }
            return {
                ok: true,
                json: async () => ({}),
            };
        });
    });

    afterEach(() => {
        document.documentElement.classList.remove("light");
        global.fetch = originalFetch;
        vi.restoreAllMocks();
    });

    test("renders upcoming match names with readable light-mode text", async () => {
        render(
            <ThemeContext.Provider value={{ theme: "light", toggleTheme: () => {} }}>
                <MemoryRouter initialEntries={["/clubs/1"]}>
                    <Routes>
                        <Route path="/clubs/:clubId" element={<ClubHome />} />
                    </Routes>
                </MemoryRouter>
            </ThemeContext.Provider>,
        );

        expect(await screen.findByText("NetRank Aces")).toHaveStyle({
            color: "#0f172a",
        });
        expect(screen.getByText("Rally Rockets")).toHaveStyle({
            color: "#0f172a",
        });
    });
});
