import { createContext, useContext } from "react";

export const LangContext = createContext(null);

export function useLangContext() {
    return useContext(LangContext);
}