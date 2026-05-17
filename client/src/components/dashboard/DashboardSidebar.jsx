// Dashboard UI component for DashboardSidebar.

import { useState } from "react";
import styles from "@/style/dashboard/Dashboard.module.css";

import navStyles from "@/style/common/Nav.module.css";
import btnStyles from "@/style/common/Buttons.module.css";

import { getDashboardTabs } from "@/components/dashboard/dashboardUtils.js";
import { HomeIcon, SignOutIcon, ThemeIcon } from "@/components/dashboard/DashboardIcons.jsx";
import { useCurrentUserContext } from "@/context/useCurrentUserContext";

export default function DashboardSidebar({
    theme,
    activeTab,
    texts,
    onTabChange,
    onThemeToggle,
    onGoHome,
    onSignOut,
}) {
    const { currentUser, loadingUser } = useCurrentUserContext();
    const tabs = getDashboardTabs(texts || {});
    /*
     Owns the mobile drawer state for the dashboard shell.
    */
    const [mobileOpen, setMobileOpen] = useState(false);

    function closeMobileMenu() {
        /*
         Closes the mobile drawer after an action completes.
        */
        setMobileOpen(false);
    }

    function handleTabChange(tabId) {
        /*
         Switches tabs and closes the mobile drawer.
        */
        onTabChange(tabId);
        closeMobileMenu();
    }

    function handleThemeToggle() {
        /*
         Toggles the dashboard theme and closes the drawer.
        */
        onThemeToggle();
        closeMobileMenu();
    }

    function handleGoHome() {
        /*
         Sends the user home and closes the drawer.
        */
        onGoHome();
        closeMobileMenu();
    }

    function handleSignOut() {
        /*
         Signs the user out and closes the mobile menu.
        */
        onSignOut();
        closeMobileMenu();
    }

    const iconButtons = (
        <>
            <button type="button" className={btnStyles.iconButton} onClick={handleThemeToggle}
                aria-label={theme === "dark" ? texts?.switch_to_light_mode : texts?.switch_to_dark_mode}
                title={theme === "dark" ? texts?.light_mode || "Light mode" : texts?.dark_mode || "Dark mode"}>
                {/* Theme toggle changes the shell colors without leaving the dashboard. */}
                <ThemeIcon isDarkMode={theme === "dark"} />
            </button>
            <button type="button" className={btnStyles.iconButton} onClick={handleGoHome}
                aria-label={texts?.go_to_home || "Go to home"} title={texts?.home || "Home"}>
                {/* Home returns to the public-facing landing page. */}
                <HomeIcon />
            </button>
            <button type="button" className={`${btnStyles.iconButton} ${styles.signOutButton}`}
                onClick={handleSignOut} aria-label={texts?.sign_out || "Sign out"} title={texts?.sign_out || "Sign out"}>
                {/* Sign out is kept in the same toolbar because it is global to the session. */}
                <SignOutIcon />
            </button>
        </>
    );

    return (
        <aside className={styles.sidebar}>
            {/* ── Desktop layout: vertical sidebar ── */}
            <div className={styles.desktopSection}>
                <div className={styles.brand}>NetRank</div>
                {/* Showing the email helps confirm which account is driving the dashboard state. */}
                <p className={styles.userValue}>
                    {loadingUser ? "Loading..." : currentUser?.email || texts?.unknown_user || "unknown"}
                </p>
                <nav className={navStyles.nav} aria-label={texts?.dashboard_tabs_aria || "Dashboard tabs"}>
                    {tabs.map((tab) => (
                        <button key={tab.id} type="button"
                            className={`${navStyles.navButton} ${activeTab === tab.id ? btnStyles.navButtonActive : ""}`}
                            onClick={() => onTabChange(tab.id)}>
                            {/* Each tab is a direct dashboard view switch, not a route change. */}
                            {tab.label}
                        </button>
                    ))}
                </nav>
                <div className={styles.sidebarFooter}>{iconButtons}</div>
            </div>

            {/* ── Mobile layout: compact top bar ── */}
            <div className={styles.mobileBar}>
                <span className={styles.brand}>NetRank</span>
                <button
                    type="button"
                    className={styles.mobileToggle}
                    onClick={() => setMobileOpen(v => !v)}
                    aria-label={mobileOpen ? "Close menu" : "Open menu"}
                    aria-expanded={mobileOpen}
                >
                    {/* The hamburger exposes the same actions as desktop without crowding narrow screens. */}
                    <span className={styles.mobileToggleIcon}>{mobileOpen ? "✕" : "☰"}</span>
                </button>
            </div>

            {/* ── Mobile dropdown ── */}
            {mobileOpen && (
                <div className={styles.mobileMenu}>
                    <div className={styles.mobileMenuHeader}>
                        <p className={styles.mobileMenuUser}>
                            {currentUser?.email || texts?.unknown_user || "unknown"}
                        </p>
                        <p className={styles.mobileActiveLabel}>
                            {tabs.find((t) => t.id === activeTab)?.label || ""}
                        </p>
                    </div>
                    <div className={styles.mobileMenuActions}>
                        {iconButtons}
                    </div>
                    <nav className={styles.mobileMenuNav}>
                        {tabs.map((tab) => (
                            <button key={tab.id} type="button"
                                className={`${styles.mobileMenuTab} ${activeTab === tab.id ? styles.mobileMenuTabActive : ""}`}
                                onClick={() => handleTabChange(tab.id)}>
                                {/* Mobile tabs close the drawer after selection so the next screen gets full width. */}
                                {tab.label}
                            </button>
                        ))}
                    </nav>
                </div>
            )}
        </aside>
    );
}
