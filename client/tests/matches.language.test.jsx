import { test, expect } from "vitest";
import { getTexts } from "virtual:i18n";

test("matches page texts exist in English and Dutch", () => {
    const enMatches = getTexts("matches", "en");
    const nlMatches = getTexts("matches", "nl");
    const enDashboard = getTexts("dashboard", "en");
    const nlDashboard = getTexts("dashboard", "nl");

    expect(enMatches.title).toBe("Weekly Match Proposals");
    expect(nlMatches.title).toBe("Wekelijkse wedstrijdvoorstellen");
    expect(enMatches.refresh).toBe("Refresh");
    expect(nlMatches.refresh).toBe("Vernieuwen");
    expect(enMatches.reset_pending).toBe("Set back to pending");
    expect(nlMatches.reset_pending).toBe("Opnieuw in afwachting zetten");
    expect(enDashboard.status_accepted).toBe("Accepted");
    expect(nlDashboard.status_accepted).toBe("Geaccepteerd");
});
