// Regression tests for setupTests.

import "@testing-library/jest-dom/vitest";
import { beforeEach, vi } from "vitest";
// Shared test helper for arranging the scenario under test.

function createMemoryStorage() {
  const store = new Map();
  return {
    getItem: (key) => (store.has(key) ? store.get(key) : null),
    setItem: (key, value) => store.set(key, String(value)),
    removeItem: (key) => store.delete(key),
    clear: () => store.clear(),
  };
}

if (
  typeof globalThis.localStorage === "undefined" ||
  typeof globalThis.localStorage?.getItem !== "function"
) {
  Object.defineProperty(globalThis, "localStorage", {
    value: createMemoryStorage(),
    configurable: true,
  });
}

beforeEach(() => {
  vi.restoreAllMocks();
  globalThis.localStorage.clear();
});
