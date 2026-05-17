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
    const [mobileOpen, setMobileOpen] = useState(false);

    function closeMobileMenu() {
        setMobileOpen(false);
    }

    function handleTabChange(tabId) {
        onTabChange(tabId);
        closeMobileMenu();
    }

    function handleThemeToggle() {
        onThemeToggle();
        closeMobileMenu();
    }

    function handleGoHome() {
        onGoHome();
        closeMobileMenu();
    }

    function handleSignOut() {
        onSignOut();
        closeMobileMenu();
    }

    const iconButtons = (
        <>
            <button type="button" className={btnStyles.iconButton} onClick={handleThemeToggle}
                aria-label={theme === "dark" ? texts?.switch_to_light_mode : texts?.switch_to_dark_mode}
                title={theme === "dark" ? texts?.light_mode || "Light mode" : texts?.dark_mode || "Dark mode"}>
                <ThemeIcon isDarkMode={theme === "dark"} />
            </button>
            <button type="button" className={btnStyles.iconButton} onClick={handleGoHome}
                aria-label={texts?.go_to_home || "Go to home"} title={texts?.home || "Home"}>
                <HomeIcon />
            </button>
            <button type="button" className={`${btnStyles.iconButton} ${styles.signOutButton}`}
                onClick={handleSignOut} aria-label={texts?.sign_out || "Sign out"} title={texts?.sign_out || "Sign out"}>
                <SignOutIcon />
            </button>
        </>
    );

    return (
        <aside className={styles.sidebar}>
            {/* ── Desktop layout: vertical sidebar ── */}
            <div className={styles.desktopSection}>
                <div className={styles.brand}>NetRank</div>
                <p className={styles.userValue}>
                    {loadingUser ? "Loading..." : currentUser?.email || texts?.unknown_user || "unknown"}
                </p>
                <nav className={navStyles.nav} aria-label={texts?.dashboard_tabs_aria || "Dashboard tabs"}>
                    {tabs.map((tab) => (
                        <button key={tab.id} type="button"
                            className={`${navStyles.navButton} ${activeTab === tab.id ? btnStyles.navButtonActive : ""}`}
                            onClick={() => onTabChange(tab.id)}>
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
                                {tab.label}
                            </button>
                        ))}
                    </nav>
                </div>
            )}
        </aside>
    );
}
