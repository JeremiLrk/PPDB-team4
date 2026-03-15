import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { notify } from "@/hooks/useNotify.js";
import Badge from "./Badge";
import styles from "@/style/Header.module.css";
import { usePageTexts } from "@/hooks/usePageTexts.js";
import { useLangContext } from "@/context/useLangContext.js";
import { useCurrentUserContext } from "@/context/useCurrentUserContext.js";

export default function Header({ status }) {
    const navigate = useNavigate();
    const [menuOpen, setMenuOpen] = useState(false);
    const dropdownRef = useRef(null);
    const { lang, setLang } = useLangContext();
    const { currentUser, setCurrentUser } = useCurrentUserContext();

    const baseTexts = usePageTexts("base", lang);
    const authTexts = usePageTexts("authorization", lang);

    useEffect(() => {
        function handleClickOutside(event) {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
                setMenuOpen(false);
            }
        }

        document.addEventListener("mousedown", handleClickOutside);
        return () => {
            document.removeEventListener("mousedown", handleClickOutside);
        };
    }, []);

    async function handleLogout() {
        try {
            const response = await fetch("/api/logout", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                credentials: "include",
            });

            const data = await response.json();
            if (!response.ok) {
                throw new Error(data?.message || "Logout failed");
            }

            setCurrentUser(null);
            notify.success("Logout successful");
            navigate("/");
        } catch (err) {
            console.error(err?.message || "Logout failed");
            notify.error(err?.message || "Logout failed");
        }
    }

    const userLabel =
        (currentUser?.firstName &&
            currentUser?.lastName &&
            `${currentUser.firstName} ${currentUser.lastName}`) ||
        authTexts.user ||
        "User";

    return (
        <header className={styles.header}>
            <div className={styles.headerInner}>
                <div>
                    <Badge status={status} />
                </div>

                <h1 className={styles.headerTitle}>
                    <button onClick={() => navigate("/")}>
                        {baseTexts.net_rank || "NetRank"}
                    </button>
                </h1>

                <div className={styles.headerRight}>
                    <button onClick={() => setLang("nl")}>NL</button>
                    <button onClick={() => setLang("en")}>EN</button>

                    {!currentUser ? (
                        <>
                            <button
                                onClick={() => navigate("/login")}
                                className={styles.headerButton}
                            >
                                {authTexts.log_in || "Log in"}
                            </button>
                            <button
                                onClick={() => navigate("/register")}
                                className={styles.headerPrimaryButton}
                            >
                                {authTexts.register || "Register"}
                            </button>
                        </>
                    ) : (
                        <div className="relative" ref={dropdownRef}>
                            <button
                                className={styles.userButton}
                                onClick={() => setMenuOpen((prev) => !prev)}
                            >
                                {userLabel} ▾
                            </button>

                            {menuOpen && (
                                <div className="absolute right-0 mt-2 z-50 rounded bg-white text-black shadow-lg">
                                    <ul className="flex flex-col p-2">
                                        <li>
                                            <button
                                                className={styles.userDropdownItem}
                                                onMouseDown={() => navigate("/dashboard")}
                                            >
                                                Dashboard
                                            </button>
                                        </li>
                                        <li>
                                            <button
                                                className={styles.userDropdownItem}
                                                onMouseDown={handleLogout}
                                            >
                                                {authTexts.log_out || "Log out"}
                                            </button>
                                        </li>
                                    </ul>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </header>
    );
}
