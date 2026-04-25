import "@testing-library/jest-dom/vitest";
import { describe, test, expect } from "vitest";

import styles from "../src/style/common/Common.module.css";
import { getDashboardTabs, statusClass, statusLabel } from "../src/components/dashboard/dashboardUtils.js";

describe("dashboardUtils", () => {
  test("getDashboardTabs returns translated labels with stable ids", () => {
    const tabs = getDashboardTabs({
      tab_overview: "Overzicht",
      tab_availability: "Beschikbaarheid",
      tab_search: "Zoek clubs",
      tab_requests: "Mijn aanvragen",
      tab_teams: "Mijn teams",
      tab_create_club: "Voeg je eigen club toe",
      tab_manage_club: "Beheer je clubs",
    });

    expect(tabs).toEqual([
      { id: "overview", label: "Overzicht" },
      { id: "availability", label: "Beschikbaarheid" },
      { id: "search", label: "Zoek clubs" },
      { id: "requests", label: "Mijn aanvragen" },
      { id: "teams", label: "Mijn teams" },
      { id: "createClub", label: "Voeg je eigen club toe" },
      { id: "manageClubs", label: "Beheer je clubs" },
    ]);
  });

  test("statusClass maps each status to Common.module.css class", () => {
    expect(statusClass("approved")).toBe(styles.statusApproved);
    expect(statusClass("rejected")).toBe(styles.statusRejected);
    expect(statusClass("cancelled")).toBe(styles.statusCancelled);
    expect(statusClass("pending")).toBe(styles.statusPending);
    expect(statusClass("unknown")).toBe(styles.statusPending);
  });

  test("statusLabel uses localized labels with fallback to English", () => {
    const texts = {
      status_approved: "Goedgekeurd",
      status_rejected: "Afgewezen",
      status_cancelled: "Geannuleerd",
      status_pending: "In behandeling",
    };

    expect(statusLabel("approved", texts)).toBe("Goedgekeurd");
    expect(statusLabel("rejected", texts)).toBe("Afgewezen");
    expect(statusLabel("cancelled", texts)).toBe("Geannuleerd");
    expect(statusLabel("pending", texts)).toBe("In behandeling");
    expect(statusLabel("other", texts)).toBe("In behandeling");
    expect(statusLabel("approved", {})).toBe("Approved");
  });
});
