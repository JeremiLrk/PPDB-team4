import { createContext, useContext } from "react";
import {useLang} from "@/hooks/useLang.js";

export const LangContext = createContext(null);

export function LangProvider({ children }) {
    const [lang, setLang] = useLang("en")

    return (
        <LangContext.Provider value={{lang, setLang}}>
            {children}
        </LangContext.Provider>
    );
}

export function useLangContext() {
    const context = useContext(LangContext);
    if (!context) {
        throw new Error("useLangContext must be used within a LangProvider");
    }
    return context;
}
