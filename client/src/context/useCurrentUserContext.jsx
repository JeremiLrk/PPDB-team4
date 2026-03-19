import { createContext, useEffect, useState, useContext } from "react";

const CurrentUserContext = createContext();

export function CurrentUserProvider({ children }) {
    const [currentUser, setCurrentUser] = useState(null);
    const [loadingUser, setLoadingUser] = useState(true);

    useEffect(() => {
        fetch("/api/me", {
            credentials: "include"
        })
            .then(res => {
                if (!res.ok) throw new Error();
                return res.json();
            })
            .then(data => setCurrentUser(data.user))
            .catch(() => setCurrentUser(null))
            .finally(() => setLoadingUser(false));
    }, []);

    return (
        <CurrentUserContext.Provider value={{ currentUser, setCurrentUser, loadingUser }}>
            {children}
        </CurrentUserContext.Provider>
    );
}

export function useCurrentUserContext() {
    return useContext(CurrentUserContext);
}

export default CurrentUserContext;