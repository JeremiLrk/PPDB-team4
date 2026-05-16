import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { notify } from "@/hooks/useNotify.js";
import Badge from "./Badge";
import styles from "@/style/Header.module.css";
import { usePageTexts } from "@/hooks/common/usePageTexts.js";
import { useLangContext } from "@/context/useLangContext.jsx";
import { useCurrentUserContext } from "@/context/useCurrentUserContext";

/** Supported UI languages displayed in the switcher. */
const SUPPORTED_LANGS = [
    { code: "en", label: "EN" },
    { code: "nl", label: "NL" },
];

export default function Header({ status }) {
    const navigate = useNavigate();
    const [menuOpen, setMenuOpen] = useState(false);
    const dropdownRef = useRef(null);

    //  i18n
    const { lang, setLang } = useLangContext();

    // usePageTexts now calls /api/i18n/page/<page>?lang=<lang>
    // backed by Flask-Babel .mo catalogues — no DB query needed.
    const baseTexts = usePageTexts("base", lang);
    const authTexts = usePageTexts("authorization", lang);

    //  current user 
    const { currentUser, setCurrentUser } = useCurrentUserContext();

    //  dropdown close on outside click 
    useEffect(() => {
        function handleClickOutside(event) {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
                setMenuOpen(false);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    //  logout 
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
            try { data = await response.json(); } catch { /* empty body */ }

            if (!response.ok) {
                throw new Error(data?.message || authTexts.log_out_failed || "Logout failed");
            }

            notify.success(authTexts.log_out_success || "Logged out");
            navigate("/");
        } catch (err) {
            // Local logout already applied; don't block navigation on backend errors.
            console.error(err?.message || authTexts.log_out_failed || "Logout failed");
            navigate("/");
        }
    }

    const userLabel =
        (currentUser?.firstName && currentUser?.lastName &&
            `${currentUser.firstName} ${currentUser.lastName}`) ||
        authTexts.account ||
        "Account";

    //  render 
    return (
        <header className={styles.header}>
            <div className={styles.headerInner}>

                {/*  Left: badge + nav  */}
                <div className={styles.headerLeft}>
                    <Badge status={status} />
                    <nav className={styles.headerNav}>
                        <button onClick={() => navigate("/clubs")} className={styles.navLink}>
                            {baseTexts.clubs || "Clubs"}
                        </button>
                        <button onClick={() => navigate("/teams")} className={styles.navLink}>
                            {baseTexts.teams || "Teams"}
                        </button>
                    </nav>
                </div>

                {/*  Centre: brand  */}
                <h1 className={styles.headerTitle}>
                    <button className={styles.brandButton} onClick={() => navigate("/")}>
                        {baseTexts.net_rank || "NetRank"}
                    </button>
                </h1>

                {/*  Right: lang switcher + auth  */}
                <div className={styles.headerRight}>

                    {/* Language switcher — highlights the active locale */}
                    <div className={styles.langSwitcher}>
                        {SUPPORTED_LANGS.map(({ code, label }) => (
                            <button
                                key={code}
                                className={`${styles.langButton} ${lang === code ? styles.langButtonActive : ""}`}
                                onClick={() => setLang(code)}
                                aria-pressed={lang === code}
                                aria-label={`Switch language to ${label}`}
                            >
                                {label}
                            </button>
                        ))}
                    </div>

                    {/* Auth buttons / user menu */}
                    {!currentUser ? (
                        <>
                            <button onClick={() => navigate("/login")} className={styles.headerButton}>
                                {authTexts.log_in}
                            </button>
                            <button onClick={() => navigate("/register")} className={styles.headerPrimaryButton}>
                                {authTexts.register || "Registreren"}
                            </button>
                        </>
                    ) : (
                        <div className={styles.userMenu} ref={dropdownRef}>
                            <button
                                className={styles.userButton}
                                onClick={() => setMenuOpen((prev) => !prev)}
                                aria-expanded={menuOpen}
                                aria-haspopup="menu"
                            >
                                {userLabel} ▾
                            </button>
                            {menuOpen && (
                                <div className={styles.userDropdown} role="menu">
                                    <ul className={styles.userDropdownList}>
                                        <li role="none">
                                            <button
                                                role="menuitem"
                                                className={styles.userDropdownItem}
                                                onClick={() => { setMenuOpen(false); navigate("/dashboard"); }}
                                            >
                                                {baseTexts.dashboard || "Dashboard"}
                                            </button>
                                        </li>
                                        <li role="none">
                                            <button
                                                role="menuitem"
                                                className={styles.userDropdownItem}
                                                onClick={handleLogout}
                                            >
                                                {authTexts.log_out || "Uitloggen"}
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
