import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
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

test("header Login button navigates to /login", async () => {
  mockHealthyBackend();
  const user = userEvent.setup();

  render(
    <MemoryRouter initialEntries={["/"]}>
      <App />
    </MemoryRouter>
  );

  const banner = screen.getByRole("banner");
  await user.click(within(banner).getByRole("button", { name: "Login" }));

  expect(await screen.findByRole("heading", { name: "Login" })).toBeInTheDocument();
});

test("header Register button navigates to /register", async () => {
  mockHealthyBackend();
  const user = userEvent.setup();

  render(
    <MemoryRouter initialEntries={["/"]}>
      <App />
    </MemoryRouter>
  );

  const banner = screen.getByRole("banner");
  await user.click(within(banner).getByRole("button", { name: "Register" }));

  expect(
    await screen.findByRole("heading", { name: "Register" })
  ).toBeInTheDocument();
});

test("home 'Join the Ladder' button navigates to Register page", async () => {
  mockHealthyBackend();
  const user = userEvent.setup();

  render(
    <MemoryRouter initialEntries={["/"]}>
      <App />
    </MemoryRouter>
  );

  await user.click(screen.getByRole("button", { name: "Join the Ladder" }));

  expect(
    await screen.findByRole("heading", { name: "Register" })
  ).toBeInTheDocument();
});

test("home ladder buttons navigate to Ladder page", async () => {
  mockHealthyBackend();
  const user = userEvent.setup();

  render(
    <MemoryRouter initialEntries={["/"]}>
      <App />
    </MemoryRouter>
  );

  await user.click(screen.getByRole("button", { name: "Men’s Tennis" }));

  expect(
    await screen.findByRole("heading", { name: "Available Ladders" })
  ).toBeInTheDocument();
});

test("register 'Continue as guest' navigates back to home", async () => {
  mockHealthyBackend();
  const user = userEvent.setup();

  render(
    <MemoryRouter initialEntries={["/register"]}>
      <App />
    </MemoryRouter>
  );

  await user.click(screen.getByRole("link", { name: "Continue as guest" }));

  expect(
    await screen.findByText("Compete. Challenge. Climb the ladder.")
  ).toBeInTheDocument();
});

test("login 'Continue as guest' navigates back to home", async () => {
  mockHealthyBackend();
  const user = userEvent.setup();

  render(
    <MemoryRouter initialEntries={["/login"]}>
      <App />
    </MemoryRouter>
  );

  await user.click(screen.getByRole("link", { name: "Continue as guest" }));

  expect(
    await screen.findByText("Compete. Challenge. Climb the ladder.")
  ).toBeInTheDocument();
});

