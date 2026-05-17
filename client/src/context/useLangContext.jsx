// React context helper for useLangContext.

import { createContext, useContext } from "react";
import {useLang} from "@/hooks/common/useLang.js";

export const LangContext = createContext(null);

export function LangProvider({ children }) {
    /*
     Stores the active language in a React context for the app tree.
    */
    const [lang, setLang] = useLang("en")

    return (
        <LangContext.Provider value={{lang, setLang}}>
            {children}
        </LangContext.Provider>
    );
}

export function useLangContext() {
    /*
     Reads the active language context for child components.
    */
    const context = useContext(LangContext);
    if (!context) {
        throw new Error("useLangContext must be used within a LangProvider");
    }
    return context;
}
