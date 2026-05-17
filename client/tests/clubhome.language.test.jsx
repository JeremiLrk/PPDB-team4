import "@testing-library/jest-dom/vitest";
import { expect, test } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

import App from "../src/app/App.jsx";
import { mockApi } from "./testApiMock.js";

// Verifies club home shows Dutch labels on the club homepage.
test("club home renders Dutch localized labels", async () => {
    localStorage.setItem("app_lang", "nl");

    mockApi({
        club: { id: 1, name: "NetRank Club", description: "Mock data club", sport: "Padel", city: "Antwerp" },
        clubs: [{ id: 1, name: "NetRank Club", description: "Mock data club", sport: "Padel", city: "Antwerp" }],
        clubHomeSummary: {
            club: { id: 1, name: "NetRank Club", description: "Mock data club", sport: "Padel", city: "Antwerp" },
            ladders: [{ id: 11, name: "Men's Singles" }],
            performers: [{ id: 1, name: "Thomas", rating: 1290 }],
            upcoming_matches: [{
                id: 21,
                team1Name: "NetRank A",
                team2Name: "Riverside B",
                ladderName: "Men's Singles League",
                status: "accepted",
                scoreStatus: "not_submitted",
                proposedStartAt: "2026-05-21T10:00:00Z",
            }, {
                id: 23,
                team1Name: "NetRank C",
                team2Name: "Riverside D",
                ladderName: "Men's Singles League",
                status: "accepted",
                scoreStatus: "not_submitted",
                proposedStartAt: "2026-05-22T10:00:00Z",
            }, {
                id: 24,
                team1Name: "NetRank E",
                team2Name: "Riverside F",
                ladderName: "Men's Singles League",
                status: "accepted",
                scoreStatus: "not_submitted",
                proposedStartAt: "2026-05-23T10:00:00Z",
            }, {
                id: 25,
                team1Name: "NetRank G",
                team2Name: "Riverside H",
                ladderName: "Men's Singles League",
                status: "accepted",
                scoreStatus: "not_submitted",
                proposedStartAt: "2026-05-24T10:00:00Z",
            }],
            latest_results: [{
                id: 22,
                team1Name: "NetRank A",
                team2Name: "Riverside B",
                ladderName: "Men's Singles League",
                status: "played",
                scoreStatus: "resolved",
                scoreTeam1: 3,
                scoreTeam2: 1,
                playedAt: "2026-05-12T10:00:00Z",
            }, {
                id: 26,
                team1Name: "NetRank C",
                team2Name: "Riverside D",
                ladderName: "Men's Singles League",
                status: "played",
                scoreStatus: "resolved",
                scoreTeam1: 2,
                scoreTeam2: 2,
                playedAt: "2026-05-13T10:00:00Z",
            }, {
                id: 27,
                team1Name: "NetRank E",
                team2Name: "Riverside F",
                ladderName: "Men's Singles League",
                status: "played",
                scoreStatus: "resolved",
                scoreTeam1: 4,
                scoreTeam2: 0,
                playedAt: "2026-05-14T10:00:00Z",
            }, {
                id: 28,
                team1Name: "NetRank G",
                team2Name: "Riverside H",
                ladderName: "Men's Singles League",
                status: "played",
                scoreStatus: "resolved",
                scoreTeam1: 1,
                scoreTeam2: 3,
                playedAt: "2026-05-15T10:00:00Z",
            }],
        },
    });

    render(
        <MemoryRouter initialEntries={["/clubs/1"]}>
            <App />
        </MemoryRouter>
    );

    // Both sections render a "load more" button because the fixture includes more than the initial 3 rows.
    expect(await screen.findByRole("heading", { name: "Uitblinkers" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Aankomende wedstrijden" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Recentste resultaten" })).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: "Meer laden" })).toHaveLength(2);

    localStorage.removeItem("app_lang");
});
