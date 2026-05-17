// Regression tests for app.smoke.test.

import "@testing-library/jest-dom/vitest";
import { test } from "vitest";
import { render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import App from "../src/app/App.jsx";
import { mockApi } from "./testApiMock.js";

// Verifies that the app shell renders and the backend health badge becomes Online.
test("renders header and shows Online status", async () => {
  localStorage.setItem("app_lang", "nl");
  mockApi();

  render(
    <MemoryRouter initialEntries={["/"]}>
      <App />
    </MemoryRouter>
  );

  const banner = screen.getByRole("banner");
  expect(within(banner).getByText("NetRank")).toBeInTheDocument();
  expect(within(banner).getByRole("button", { name: "Inloggen" })).toBeInTheDocument();
  expect(within(banner).getByRole("button", { name: "Registreren" })).toBeInTheDocument();

  expect(await screen.findByText("Online")).toBeInTheDocument();
  localStorage.removeItem("app_lang");
});
