import { createContext, useContext } from "react";

export const ThemeContext = createContext({
    theme: "dark",
    toggleTheme: () => {},
});

export function useThemeContext() {
    return useContext(ThemeContext);
}
