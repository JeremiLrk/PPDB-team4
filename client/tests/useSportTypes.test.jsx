// Regression tests for useSportTypes helpers.

import "@testing-library/jest-dom/vitest";
import { describe, expect, test } from "vitest";

import { sortSportTypes } from "../src/hooks/useSportTypes.js";

describe("sortSportTypes", () => {
    test("prioritizes tennis and padel before other sports", () => {
        const sorted = sortSportTypes([
            { id: 3, name: "Basketball" },
            { id: 1, name: "Padel" },
            { id: 4, name: "Badminton" },
            { id: 2, name: "Tennis" },
        ]);

        expect(sorted.map((sport) => sport.name)).toEqual([
            "Tennis",
            "Padel",
            "Badminton",
            "Basketball",
        ]);
    });
});
