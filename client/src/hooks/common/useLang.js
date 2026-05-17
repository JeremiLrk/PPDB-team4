// Shared hook for useLang.

import { useState} from "react";

const LANG_KEY = "app_lang";  // key for localStorage

export function useLang(defaultLang = "en") {
    /*
     Stores the active UI language and persists it in localStorage.
    */
    const [lang, setLangState] = useState(
        () => localStorage.getItem(LANG_KEY) || defaultLang
    );

    function setLang(newLang) {
        /*
         Saves the selected language and updates the hook state.
        */
        localStorage.setItem(LANG_KEY, newLang);
        setLangState(newLang);
    }

    return [lang, setLang];
}
