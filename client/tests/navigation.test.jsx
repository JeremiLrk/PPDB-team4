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
    const user = userEvent.setup();

    render(
        <MemoryRouter initialEntries={["/"]}>
            <App />
        </MemoryRouter>
    );

    const banner = screen.getByRole("banner");
    await user.click(within(banner).getByRole("button", { name: "Log in" }));

    expect(await screen.findByRole("heading", { name: "Log in" })).toBeInTheDocument();
});

// Verifies header Register button navigates to the register page.
test("header Register button navigates to /register", async () => {
    mockApi();
    const user = userEvent.setup();

    render(
        <MemoryRouter initialEntries={["/"]}>
            <App />
        </MemoryRouter>
    );

    const banner = screen.getByRole("banner");
    await user.click(within(banner).getByRole("button", { name: "Register" }));

    expect(await screen.findByRole("heading", { name: "Register" })).toBeInTheDocument();
});

// Verifies landing Explore clubs button opens the clubs overview page.
test("landing Explore clubs button navigates to /clubs", async () => {
    mockApi();
    const user = userEvent.setup();

    render(
        <MemoryRouter initialEntries={["/"]}>
            <App />
        </MemoryRouter>
    );

    await user.click(screen.getByRole("button", { name: "Explore clubs" }));

    expect(await screen.findByRole("heading", { name: "All Clubs" })).toBeInTheDocument();
});

// Verifies dashboard button redirects anonymous users to login.
test("landing Open dashboard sends anonymous user to /login", async () => {
    mockApi({ me: null });
    const user = userEvent.setup();

    render(
        <MemoryRouter initialEntries={["/"]}>
            <App />
        </MemoryRouter>
    );

    await user.click(screen.getByRole("button", { name: "Open dashboard" }));
    expect(await screen.findByRole("heading", { name: "Log in" })).toBeInTheDocument();
});

// Verifies register page guest link returns to landing page.
test("register Continue as guest navigates back to landing", async () => {
    mockApi();
    const user = userEvent.setup();

    render(
        <MemoryRouter initialEntries={["/register"]}>
            <App />
        </MemoryRouter>
    );

    await user.click(await screen.findByRole("link", { name: "Continue as guest" }));
    expect(await screen.findByRole("heading", { name: "How NetRank works" })).toBeInTheDocument();
});

// Verifies login page guest link returns to landing page.
test("login Continue as guest navigates back to landing", async () => {
    mockApi();
    const user = userEvent.setup();

    render(
        <MemoryRouter initialEntries={["/login"]}>
            <App />
        </MemoryRouter>
    );

    await user.click(await screen.findByRole("link", { name: "Continue as guest" }));
    expect(await screen.findByRole("heading", { name: "How NetRank works" })).toBeInTheDocument();
});
