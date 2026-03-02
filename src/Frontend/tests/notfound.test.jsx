import { render, screen } from "@testing-library/react";
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

test("unknown route shows 404 page", async () => {
  mockHealthyBackend();

  render(
    <MemoryRouter initialEntries={["/doesn't exist"]}>
      <App />
    </MemoryRouter>
  );

  expect(
    await screen.findByRole("heading", { name: "404 - Page Not Found" })
  ).toBeInTheDocument();
});

