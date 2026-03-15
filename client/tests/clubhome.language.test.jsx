import "@testing-library/jest-dom/vitest";
import { test } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

import App from "../src/app/App.jsx";
import { mockApi } from "./testApiMock.js";

// Verifies club home shows Dutch labels for top players and pending match status.
test("club home renders Dutch localized labels", async () => {
    localStorage.setItem("app_lang", "nl");

    mockApi({
        club: { id: 1, name: "NetRank Club" },
        clubs: [{ id: 1, name: "NetRank Club" }],
        topPlayers: [{ id: 1, name: "Thomas", rating: 1290 }],
    });

    render(
        <MemoryRouter initialEntries={["/clubs/1"]}>
            <App />
        </MemoryRouter>
    );

    expect(await screen.findByRole("heading", { name: "Topspelers" })).toBeInTheDocument();
    expect(screen.getAllByText("In behandeling").length).toBeGreaterThan(0);

    localStorage.removeItem("app_lang");
});
