import { createContext, useContext } from "react";

export const CurrentUserContext = createContext(null);

export function useCurrentUserContext() {
    return useContext(CurrentUserContext);
}