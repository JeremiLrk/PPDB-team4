// React context helper for useThemeContext.

import { createContext, useContext } from "react";

export const ThemeContext = createContext({
    theme: "dark",
    toggleTheme: () => {},
});

export function useThemeContext() {
    /*
     Exposes the current theme context to the calling component.
    */
    return useContext(ThemeContext);
}
