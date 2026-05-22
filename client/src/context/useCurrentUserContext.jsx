// React context helper for useCurrentUserContext.

import { createContext, useEffect, useState, useContext, useCallback } from "react";

const CurrentUserContext = createContext();

export function CurrentUserProvider({ children }) {
    /*
     Stores the authenticated user and loads it once on mount.
    */
    const [currentUser, setCurrentUser] = useState(null);
    const [loadingUser, setLoadingUser] = useState(true);

    const reloadCurrentUser = useCallback(async () => {
        /*
         Fetches the current session user from the backend.
         Callers use this after role-changing actions so the shared context
         stays in sync without a full page refresh.
        */
        try {
            const response = await fetch("/api/me", {
                credentials: "include"
            });

            if (!response.ok) {
                setCurrentUser(null);
                return null;
            }

            const data = await response.json();
            const account = data?.account ?? null;
            setCurrentUser(account);
            return account;
        } catch {
            setCurrentUser(null);
            return null;
        } finally {
            setLoadingUser(false);
        }
    }, []);

    useEffect(() => {
        /*
         Loads the current session user once on mount.
        */
        void reloadCurrentUser();
    }, [reloadCurrentUser]);

    return (
        <CurrentUserContext.Provider value={{ currentUser, setCurrentUser, loadingUser, reloadCurrentUser }}>
            {children}
        </CurrentUserContext.Provider>
    );
}

export function useCurrentUserContext() {
    return useContext(CurrentUserContext);
}

export default CurrentUserContext;
