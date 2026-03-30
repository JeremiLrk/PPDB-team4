import "@testing-library/jest-dom/vitest";
import { test } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";

import Dashboard from "../src/pages/Dashboard.jsx";
import { LangContext } from "../src/context/useLangContext.js";
import { mockApi } from "./testApiMock.js";

// Verifies dashboard tab labels and search placeholder render in Dutch.
test("dashboard renders Dutch texts when language is nl", async () => {
    mockApi({
        dashboardData: {
            roles: ["user"],
            clubs: [{ id: 1, name: "NetRank Club", description: "Mock data club", sport: "Padel", city: "Antwerp", membership_status: "member" }],
            pending_requests: { my_requests: [], my_club_creation_requests: [] },
        },
        clubs: [{ id: 1, name: "NetRank Club", description: "Mock data club", sport: "Padel", city: "Antwerp" }],
    });

    const account = userEvent.setup();

    render(
        <MemoryRouter>
            <LangContext.Provider value={{ lang: "nl", setLang: () => {} }}>
                <Dashboard
                    currentUser={{ id: 7, email: "demo@netrank.com" }}
                    setUser={() => {}}
                />
            </LangContext.Provider>
        </MemoryRouter>
    );

    expect(await screen.findByText("Ingelogd als")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Overzicht" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Zoek clubs" })).toBeInTheDocument();

    await account.click(screen.getByRole("button", { name: "Zoek clubs" }));
    expect(await screen.findByPlaceholderText("Zoek op clubnaam")).toBeInTheDocument();
});
