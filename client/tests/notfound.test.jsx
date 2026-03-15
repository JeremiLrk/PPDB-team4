import "@testing-library/jest-dom/vitest";
import { test } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

import App from "../src/app/App.jsx";
import { mockApi } from "./testApiMock.js";

// Verifies unknown URLs render the 404 page.
test("unknown route shows 404 page", async () => {
  mockApi();

  render(
    <MemoryRouter initialEntries={["/doesn't exist"]}>
      <App />
    </MemoryRouter>
  );

  expect(
    await screen.findByRole("heading", { name: "404 - Page Not Found" })
  ).toBeInTheDocument();
});
