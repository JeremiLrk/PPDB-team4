import "@testing-library/jest-dom/vitest";
import { test } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";

import App from "../src/app/App.jsx";
import { mockApi } from "./testApiMock.js";

// Verifies landing texts switch from English to Dutch through the header language toggle.
test("landing switches from EN to NL using header language toggle", async () => {
    mockApi();
    const account = userEvent.setup();

    render(
        <MemoryRouter initialEntries={["/"]}>
            <App />
        </MemoryRouter>
    );

    expect(await screen.findByRole("heading", { name: "How NetRank works" })).toBeInTheDocument();

    const banner = screen.getByRole("banner");
    await account.click(within(banner).getByRole("button", { name: "NL" }));

    expect(await screen.findByRole("heading", { name: "Hoe NetRank werkt" })).toBeInTheDocument();
});
