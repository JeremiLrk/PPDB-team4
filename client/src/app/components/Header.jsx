import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { notify } from "@/hooks/useNotify.js";
import Badge from "./Badge";
import styles from "@/style/Header.module.css";
import { usePageTexts } from "@/hooks/usePageTexts.js";
import { useLangContext } from "@/context/useLangContext.js";
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
                                <div 
                                    className="absolute right-0 mt-2 z-50 shadow-2xl"
                                    style={{ 
                                        minWidth: '180px',
                                        /* Deep Indigo/Blue transparent background */
                                        backgroundColor: 'rgba(30, 27, 75, 0.85)', 
                                        backdropFilter: 'blur(12px)',
                                        borderRadius: '12px',
                                        /* Bright Indigo border to catch the glow */
                                        border: '1px solid rgba(129, 140, 248, 0.3)',
                                        padding: '6px',
                                        boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.4), 0 0 15px rgba(99, 102, 241, 0.1)'
                                    }}
                                >
                                    <ul className="flex flex-col m-0 p-0 list-none">
                                        <li style={{ marginBottom: '2px' }}>
                                            <button
                                                className={styles.userDropdownItem}
                                                onMouseDown={() => navigate("/dashboard")}
                                                style={{ 
                                                    width: '100%', 
                                                    textAlign: 'left', 
                                                    padding: '12px 16px',
                                                    fontSize: '14px',
                                                    fontWeight: '500',
                                                    color: '#e0e7ff', // Light indigo text
                                                    borderRadius: '8px',
                                                    display: 'block',
                                                    background: 'none',
                                                    border: 'none',
                                                    cursor: 'pointer',
                                                    transition: 'background 0.2s'
                                                }}
                                            >
                                                Dashboard
                                            </button>
                                        </li>
                                        <li style={{ borderTop: '1px solid rgba(255, 255, 255, 0.1)', marginTop: '4px', paddingTop: '4px' }}>
                                            <button
                                                className={styles.userDropdownItem}
                                                onMouseDown={handleLogout}
                                                style={{ 
                                                    width: '100%', 
                                                    textAlign: 'left', 
                                                    padding: '12px 16px',
                                                    fontSize: '14px',
                                                    fontWeight: '600',
                                                    color: '#fda4af', // Soft rose/red for logout
                                                    borderRadius: '8px',
                                                    display: 'block',
                                                    background: 'none',
                                                    border: 'none',
                                                    cursor: 'pointer'
                                                }}
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
