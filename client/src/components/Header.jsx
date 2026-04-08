import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { notify } from "@/hooks/useNotify.js";
import Badge from "./Badge";
import styles from "@/style/Header.module.css";
import { usePageTexts } from "@/hooks/usePageTexts.js";
import { useLangContext } from "@/context/useLangContext.jsx";
import { useCurrentUserContext } from "@/context/useCurrentUserContext";

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
        setMenuOpen(false);
        setCurrentUser(null);
        localStorage.removeItem("currentUser");
        try {
            const response = await fetch("/api/logout", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                credentials: "include",
            });

            let data = {};
            try {
                data = await response.json();
            } catch {
                data = {};
            }
            if (!response.ok) {
                throw new Error(data?.message || "Logout failed");
            }

            notify.success("Logout successful");
            navigate("/");
        } catch (err) {
            // Local logout already happened; backend failure should not keep user stuck.
            console.error(err?.message || "Logout request failed");
            navigate("/");
        }
    }

    const userLabel =
        (currentUser?.firstName &&
            currentUser?.lastName &&
            `${currentUser.firstName} ${currentUser.lastName}`) ||
        authTexts.account ||
        "Account";

    return (
        <header className={styles.header}>
            <div className={styles.headerInner}>
                <div className={styles.headerLeft}>
                    <Badge status={status} />
                    <nav className={styles.headerNav}>
                        <button
                            onClick={() => navigate("/clubs")}
                            className={styles.navLink}
                        >
                            {baseTexts.clubs || "Clubs"}
                        </button>
                        <button
                            onClick={() => navigate("/teams")}
                            className={styles.navLink}
                        >
                            {baseTexts.teams || "Teams"}
                        </button>
                    </nav>
                </div>

                <h1 className={styles.headerTitle}>
                    <button className={styles.brandButton} onClick={() => navigate("/")}>
                        {baseTexts.net_rank || "NetRank"}
                    </button>
                </h1>

                <div className={styles.headerRight}>
                    <button className={styles.langButton} onClick={() => setLang("nl")}>NL</button>
                    <button className={styles.langButton} onClick={() => setLang("en")}>EN</button>

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
                        <div className={styles.userMenu} ref={dropdownRef}>
                            <button
                                className={styles.userButton}
                                onClick={() => setMenuOpen((prev) => !prev)}
                            >
                                {userLabel} ▾
                            </button>
                            {menuOpen && (
                                <div className={styles.userDropdown}>
                                    <ul className={styles.userDropdownList}>
                                        <li>
                                            <button
                                                className={styles.userDropdownItem}
                                                onClick={() => {
                                                    setMenuOpen(false);
                                                    navigate("/dashboard");
                                                }}
                                            >
                                                Dashboard
                                            </button>
                                        </li>
                                        <li>
                                            <button
                                                className={styles.userDropdownItem}
                                                onClick={handleLogout}
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
