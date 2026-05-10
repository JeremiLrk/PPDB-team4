/**
 * Vite plugin: reads .po files from ../server/translations/<lang>/LC_MESSAGES/messages.po
 * and embeds all translations into the bundle as a virtual module `virtual:i18n`.
 *
 * In dev mode: automatic HMR when changing any .po file.
 * In prod build: translations are embedded into the bundle, zero HTTP requests.
 *
 * Usage in components:
 * import { getTexts } from 'virtual:i18n'
 * const texts = getTexts('base', lang) // → { clubs: 'Clubs', … }
 */

import fs from "node:fs";
import path from "node:path";

const VIRTUAL_ID = "virtual:i18n";
const RESOLVED_ID = "\0virtual:i18n";

/**
 * A minimal .po parser with no external dependencies.
 * Returns { msgid: msgstr } for all non-empty pairs.
 */
function parsePo(content) {
    const result = {};
    const blocks = content.split(/\n\s*\n/);

    for (const block of blocks) {
        const idMatch = block.match(/^msgid\s+"((?:[^"\\]|\\.)*)"/m);
        const strMatch = block.match(/^msgstr\s+"((?:[^"\\]|\\.)*)"/m);
        if (!idMatch || !strMatch) continue;

        const msgid = idMatch[1].replace(/\\n/g, "\n").replace(/\\"/g, '"');
        const msgstr = strMatch[1].replace(/\\n/g, "\n").replace(/\\"/g, '"');

        if (msgid && msgstr) {
            result[msgid] = msgstr;
        }
    }
    return result;
}

/**
 * Loads all locales from translationsDir.
 * Reads all *.po files from each LC_MESSAGES/ folder and merges them.
 * Returns { en: { 'base.clubs': 'Clubs', … }, nl: { … } }
 */
function loadAllLocales(translationsDir) {
    const locales = {};

    if (!fs.existsSync(translationsDir)) {
        console.warn(`[i18n] translations dir not found: ${translationsDir}`);
        return locales;
    }

    for (const lang of fs.readdirSync(translationsDir)) {
        const lcDir = path.join(translationsDir, lang, "LC_MESSAGES");
        if (!fs.existsSync(lcDir)) continue;

        locales[lang] = {};

        const poFiles = fs.readdirSync(lcDir).filter(f => f.endsWith(".po"));
        for (const file of poFiles) {
            const content = fs.readFileSync(path.join(lcDir, file), "utf8");
            Object.assign(locales[lang], parsePo(content));
        }
    }

    return locales;
}

/**
 * Generates virtual module code.
 *
 * Exports:
 * LOCALES — { en: { 'base.clubs': 'Clubs' }, nl: { … } }
 * getTexts(page, lang) → { key: value } (without page prefix)
 * SUPPORTED_LOCALES — ['en', 'nl']
 */
function generateModuleCode(locales) {
    const json = JSON.stringify(locales);
    return `
export const LOCALES = ${json};
export const SUPPORTED_LOCALES = ${JSON.stringify(Object.keys(locales))};

/**
 * Returns all rows for the given page and language.
 * If language is not found, fallback to 'en'.
 *
 * @param {string} page — e.g. 'base', 'authorization'
 * @param {string} lang — e.g. 'en', 'nl'
 * @returns {Record<string, string>}
 */
export function getTexts(page, lang) {
    const catalogue = LOCALES[lang] ?? LOCALES['en'] ?? {};
    const prefix = page + '.';
    const out = {};
    for (const [key, val] of Object.entries(catalogue)) {
        if (key.startsWith(prefix)) {
            out[key.slice(prefix.length)] = val;
        }
    }
    return out;
}
`.trim();
}

export default function i18nPlugin(options = {}) {
    // The server/translations/ directory is relative to the project root (client/)
    const translationsDir = options.translationsDir
        ?? path.resolve(process.cwd(), "../server/translations");

    let poFiles = [];

    return {
        name: "vite-plugin-i18n",

        resolveId(id) {
            if (id === VIRTUAL_ID) return RESOLVED_ID;
        },

        load(id) {
            if (id !== RESOLVED_ID) return;

            const locales = loadAllLocales(translationsDir);

            // Save the paths of all .po for watch
            poFiles = Object.keys(locales).flatMap(lang => {
                const lcDir = path.join(translationsDir, lang, "LC_MESSAGES");
                if (!fs.existsSync(lcDir)) return [];
                return fs.readdirSync(lcDir)
                    .filter(f => f.endsWith(".po"))
                    .map(f => path.join(lcDir, f));
            });
            poFiles.forEach(f => this.addWatchFile(f));

            return generateModuleCode(locales);
        },

        // HMR: when changing .po — disable the module
        handleHotUpdate({ file, server }) {
            if (poFiles.includes(file)) {
                const mod = server.moduleGraph.getModuleById(RESOLVED_ID);
                if (mod) {
                    server.moduleGraph.invalidateModule(mod);
                    server.ws.send({ type: "full-reload" });
                }
            }
        },
    };
}