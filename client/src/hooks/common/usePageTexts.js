import { useMemo } from "react";
import { getTexts } from "virtual:i18n";

/**
 * Returns translations for the given page and language.
 *
 * The data is bundled with the Vite plugin (vite-plugin-i18n.js) —
 * no HTTP requests are made.
 *
 * The API is identical to the old hook: { key: translatedString }
 */
export function usePageTexts(page, lang = "en") {
    return useMemo(() => getTexts(page, lang), [page, lang]);
}