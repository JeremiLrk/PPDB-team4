// Regression tests for navigation.test.

import "@testing-library/jest-dom/vitest";
import { test, beforeEach, afterEach } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";

import App from "../src/app/App.jsx";
import { mockApi } from "./testApiMock.js";

beforeEach(() => {
    localStorage.setItem("app_lang", "nl");
});

afterEach(() => {
    localStorage.removeItem("app_lang");
});

// Verifies header Log in button navigates to the login page.
test("header Inloggen button navigates to /login", async () => {
    mockApi();
    const account = userEvent.setup();

    render(
        <MemoryRouter initialEntries={["/"]}>
            <App />
        </MemoryRouter>
    );

    const banner = screen.getByRole("banner");
    await account.click(within(banner).getByRole("button", { name: "Inloggen" }));

    expect(await screen.findByRole("heading", { name: "Inloggen" })).toBeInTheDocument();
});

// Verifies header Register button navigates to the register page.
// Verifies the header register button opens the registration page.
test("header Registreren button navigates to /register", async () => {
    mockApi();
    const account = userEvent.setup();

    render(
        <MemoryRouter initialEntries={["/"]}>
            <App />
        </MemoryRouter>
    );

    const banner = screen.getByRole("banner");
    await account.click(within(banner).getByRole("button", { name: "Registreren" }));

    expect(await screen.findByRole("heading", { name: "Registreren" })).toBeInTheDocument();
});

// Verifies landing Explore clubs button opens the clubs overview page.
// Verifies the landing page clubs button opens the clubs list.
test("landing Explore clubs button navigates to /clubs", async () => {
    mockApi();
    const account = userEvent.setup();

    render(
        <MemoryRouter initialEntries={["/"]}>
            <App />
        </MemoryRouter>
    );

    await account.click(await screen.findByRole("button", { name: "Verken clubs" }));

    expect(await screen.findByRole("heading", { name: "Alle clubs" })).toBeInTheDocument();
});

// Verifies dashboard button redirects anonymous users to login.
// Verifies anonymous users get redirected to login from the dashboard entry point.
test("landing Open dashboard sends anonymous account to /login", async () => {
    mockApi({ me: null });
    const account = userEvent.setup();

    render(
        <MemoryRouter initialEntries={["/"]}>
            <App />
        </MemoryRouter>
    );

    await account.click(await screen.findByRole("button", { name: "Open dashboard" }));
    expect(await screen.findByRole("heading", { name: "Inloggen" })).toBeInTheDocument();
});

// Verifies register page guest link returns to landing page.
// Verifies the guest link on register returns to the landing page.
test("register Continue as guest navigates back to landing", async () => {
    mockApi();
    const account = userEvent.setup();

    render(
        <MemoryRouter initialEntries={["/register"]}>
            <App />
        </MemoryRouter>
    );

    await account.click(await screen.findByRole("link", { name: "Doorgaan als gast" }));
    expect(await screen.findByRole("heading", { name: "Hoe NetRank werkt" })).toBeInTheDocument();
});

// Verifies login page guest link returns to landing page.
// Verifies the guest link on login returns to the landing page.
test("login Continue as guest navigates back to landing", async () => {
    mockApi();
    const account = userEvent.setup();

    render(
        <MemoryRouter initialEntries={["/login"]}>
            <App />
        </MemoryRouter>
    );

    await account.click(await screen.findByRole("link", { name: "Doorgaan als gast" }));
    expect(await screen.findByRole("heading", { name: "Hoe NetRank werkt" })).toBeInTheDocument();
});

// Verifies header Teams button opens the teams list page.
// Verifies the header teams button opens the teams list.
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
// Verifies clicking a team row opens that team's detail page.
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
// Verifies the team detail gear opens the team settings page.
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

    await user.click(await screen.findByRole("button", { name: "Instellingen voor NetRank Aces" }));
    expect(await screen.findByRole("button", { name: /<- NetRank Aces/i })).toBeInTheDocument();
});

// Verifies dashboard Teams tab "Open" action navigates to team detail.
// Verifies the dashboard teams tab open button navigates to the team detail page.
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

    await user.click(await screen.findByRole("button", { name: "Open dashboard" }));
    await user.click(await screen.findByRole("button", { name: "Mijn teams" }));
    await user.click(await screen.findByRole("button", { name: "Openen" }));

    expect(await screen.findByRole("heading", { name: "NetRank Aces" })).toBeInTheDocument();
});
