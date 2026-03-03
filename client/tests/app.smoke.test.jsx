import { render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { vi } from "vitest";

import App from "../src/App.jsx";

function mockHealthyBackend() {
  globalThis.fetch = vi.fn(async (url) => {
    if (url === "/api/health") {
      return {
        ok: true,
        json: async () => ({ db_connected: true }),
      };
    }
    throw new Error(`Unexpected fetch call in test: ${String(url)}`);
  });
}

test("renders header and shows Online status", async () => {
  mockHealthyBackend();

  render(
    <MemoryRouter initialEntries={["/"]}>
      <App />
    </MemoryRouter>
  );

  const banner = screen.getByRole("banner");
  expect(within(banner).getByText("NetRank")).toBeInTheDocument();
  expect(within(banner).getByRole("button", { name: "Login" })).toBeInTheDocument();
  expect(within(banner).getByRole("button", { name: "Register" })).toBeInTheDocument();

  // After the healthcheck, the badge should become 'Online'
  expect(await screen.findByText("Online")).toBeInTheDocument();
});

