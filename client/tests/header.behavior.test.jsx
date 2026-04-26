import "@testing-library/jest-dom/vitest";
import { test, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, useLocation } from "react-router-dom";

import Header from "../src/components/Header.jsx";
import { LangContext } from "../src/context/useLangContext.jsx";
import CurrentUserContext from "../src/context/useCurrentUserContext.jsx";

vi.mock("@/hooks/useNotify.js", () => ({
  notify: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

vi.mock("@/hooks/common/usePageTexts.js", () => ({
  usePageTexts: (page) => {
    if (page === "base") {
      return { net_rank: "NetRank", clubs: "Clubs", teams: "Teams" };
    }
    return { log_out: "Uitloggen", user: "User" };
  },
}));

function PathnameProbe() {
  const location = useLocation();
  return <div data-testid="pathname">{location.pathname}</div>;
}

function renderHeader({ currentUser, setCurrentUser = vi.fn(), setLang = vi.fn() }) {
  return {
    setCurrentUser,
    setLang,
    ...render(
      <MemoryRouter initialEntries={["/"]}>
        <LangContext.Provider value={{ lang: "en", setLang }}>
          <CurrentUserContext.Provider value={{ currentUser, setCurrentUser }}>
            <Header status="ok" />
            <PathnameProbe />
          </CurrentUserContext.Provider>
        </LangContext.Provider>
      </MemoryRouter>
    ),
  };
}

beforeEach(() => {
  global.fetch = vi.fn();
});

test("authenticated user can open menu and navigate to dashboard", async () => {
  const user = userEvent.setup();

  renderHeader({
    currentUser: { firstName: "Demo", lastName: "User", email: "demo@netrank.test" },
  });

  await user.click(screen.getByRole("button", { name: "Demo User ▾" }));
  await user.click(screen.getByRole("button", { name: "Dashboard" }));

  expect(screen.getByTestId("pathname")).toHaveTextContent("/dashboard");
});

test("logout clears local auth state and returns to landing page", async () => {
  const user = userEvent.setup();
  const setCurrentUser = vi.fn();
  localStorage.setItem("currentUser", JSON.stringify({ email: "demo@netrank.test" }));

  global.fetch.mockResolvedValue({
    ok: true,
    json: async () => ({ message: "ok" }),
  });

  renderHeader({
    currentUser: { firstName: "Demo", lastName: "User", email: "demo@netrank.test" },
    setCurrentUser,
  });

  await user.click(screen.getByRole("button", { name: "Demo User ▾" }));
  await user.click(screen.getByRole("button", { name: "Uitloggen" }));

  await waitFor(() => {
    expect(global.fetch).toHaveBeenCalledWith(
      "/api/logout",
      expect.objectContaining({ method: "POST", credentials: "include" })
    );
  });

  expect(setCurrentUser).toHaveBeenCalledWith(null);
  expect(localStorage.getItem("currentUser")).toBeNull();
  expect(screen.getByTestId("pathname")).toHaveTextContent("/");
});
