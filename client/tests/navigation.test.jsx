import "@testing-library/jest-dom/vitest";
import { test } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";

import App from "../src/app/App.jsx";
import { mockApi } from "./testApiMock.js";

// Verifies header Log in button navigates to the login page.
test("header Log in button navigates to /login", async () => {
    mockApi();
    const account = userEvent.setup();

    render(
        <MemoryRouter initialEntries={["/"]}>
            <App />
        </MemoryRouter>
    );

    const banner = screen.getByRole("banner");
    await account.click(within(banner).getByRole("button", { name: "Log in" }));

    expect(await screen.findByRole("heading", { name: "Log in" })).toBeInTheDocument();
});

// Verifies header Register button navigates to the register page.
test("header Register button navigates to /register", async () => {
    mockApi();
    const account = userEvent.setup();

    render(
        <MemoryRouter initialEntries={["/"]}>
            <App />
        </MemoryRouter>
    );

    const banner = screen.getByRole("banner");
    await account.click(within(banner).getByRole("button", { name: "Register" }));

    expect(await screen.findByRole("heading", { name: "Register" })).toBeInTheDocument();
});

// Verifies landing Explore clubs button opens the clubs overview page.
test("landing Explore clubs button navigates to /clubs", async () => {
    mockApi();
    const account = userEvent.setup();

    render(
        <MemoryRouter initialEntries={["/"]}>
            <App />
        </MemoryRouter>
    );

    await account.click(screen.getByRole("button", { name: "Explore clubs" }));

    expect(await screen.findByRole("heading", { name: "All Clubs" })).toBeInTheDocument();
});

// Verifies dashboard button redirects anonymous users to login.
test("landing Open dashboard sends anonymous account to /login", async () => {
    mockApi({ me: null });
    const account = userEvent.setup();

    render(
        <MemoryRouter initialEntries={["/"]}>
            <App />
        </MemoryRouter>
    );

    await account.click(screen.getByRole("button", { name: "Open dashboard" }));
    expect(await screen.findByRole("heading", { name: "Log in" })).toBeInTheDocument();
});

// Verifies register page guest link returns to landing page.
test("register Continue as guest navigates back to landing", async () => {
    mockApi();
    const account = userEvent.setup();

    render(
        <MemoryRouter initialEntries={["/register"]}>
            <App />
        </MemoryRouter>
    );

    await account.click(await screen.findByRole("link", { name: "Continue as guest" }));
    expect(await screen.findByRole("heading", { name: "How NetRank works" })).toBeInTheDocument();
});

// Verifies login page guest link returns to landing page.
test("login Continue as guest navigates back to landing", async () => {
    mockApi();
    const account = userEvent.setup();

    render(
        <MemoryRouter initialEntries={["/login"]}>
            <App />
        </MemoryRouter>
    );

    await account.click(await screen.findByRole("link", { name: "Continue as guest" }));
    expect(await screen.findByRole("heading", { name: "How NetRank works" })).toBeInTheDocument();
});

// Verifies header Teams button opens the teams list page.
test("header Teams button navigates to /teams", async () => {
    mockApi();
    const user = userEvent.setup();

    render(
        <MemoryRouter initialEntries={["/"]}>
            <App />
        </MemoryRouter>
    );

    const banner = screen.getByRole("banner");
    await user.click(within(banner).getByRole("button", { name: "Teams" }));

    expect(await screen.findByRole("heading", { name: "Teams" })).toBeInTheDocument();
});

// Verifies selecting a team from the teams list opens team detail.
test("teams list card click navigates to /teams/:teamId", async () => {
    mockApi({
        teams: [{ id: 201, name: "NetRank Aces", clubId: 1, sportTypeId: 4 }],
    });
    const user = userEvent.setup();

    render(
        <MemoryRouter initialEntries={["/teams"]}>
            <App />
        </MemoryRouter>
    );

    await user.click(await screen.findByRole("button", { name: /NetRank Aces/i }));
    expect(await screen.findByRole("heading", { name: "NetRank Aces" })).toBeInTheDocument();
});

// Verifies managed team detail page can navigate to team settings via gear button.
test("team detail settings gear navigates to /teams/:teamId/settings", async () => {
    mockApi({
        me: {
            id: 7,
            email: "manager@netrank.com",
            role: "team_manager",
            managedTeamIds: [201],
            clubIds: [],
        },
        teams: [{ id: 201, name: "NetRank Aces", clubId: 1, sportTypeId: 4 }],
    });
    const user = userEvent.setup();

    render(
        <MemoryRouter initialEntries={["/teams/201"]}>
            <App />
        </MemoryRouter>
    );

    await user.click(await screen.findByRole("button", { name: "Settings for NetRank Aces" }));
    expect(await screen.findByRole("button", { name: /<- NetRank Aces/i })).toBeInTheDocument();
});

// Verifies dashboard Teams tab "Open" action navigates to team detail.
test("dashboard teams tab open button navigates to /teams/:teamId", async () => {
    mockApi({
        me: {
            id: 9,
            email: "demo@netrank.com",
            role: "user",
            managedTeamIds: [],
            clubIds: [],
        },
        teams: [{ id: 201, name: "NetRank Aces", clubId: 1, sportTypeId: 4 }],
    });
    const user = userEvent.setup();

    render(
        <MemoryRouter initialEntries={["/"]}>
            <App />
        </MemoryRouter>
    );

    await user.click(screen.getByRole("button", { name: "Open dashboard" }));
    await user.click(await screen.findByRole("button", { name: "My Teams" }));
    await user.click(await screen.findByRole("button", { name: "Open" }));

    expect(await screen.findByRole("heading", { name: "NetRank Aces" })).toBeInTheDocument();
});
