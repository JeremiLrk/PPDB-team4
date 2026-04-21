import { useState} from "react";

const LANG_KEY = "app_lang";  // key for localStorage

export function useLang(defaultLang = "en") {
    const [lang, setLangState] = useState(
        () => localStorage.getItem(LANG_KEY) || defaultLang  // Restore from localStorage
    );

    function setLang(newLang) {
        localStorage.setItem(LANG_KEY, newLang);  // Save selection
        setLangState(newLang);
    }

    return [lang, setLang];
}