import styles from "@/style/Dashboard.module.css";
import { getDashboardTabs } from "@/app/components/dashboard/dashboardUtils.js";
import { HomeIcon, SignOutIcon, ThemeIcon } from "@/app/components/dashboard/DashboardIcons.jsx";

export default function DashboardSidebar({
    currentUser,
    theme,
    activeTab,
    texts,
    onTabChange,
    onThemeToggle,
    onGoHome,
    onSignOut,
}) {
    const tabs = getDashboardTabs(texts || {});

    return (
        <aside className={styles.sidebar}>
            <div className={styles.brand}>NetRank</div>

            <div className={styles.userPanel}>
                <p className={styles.userLabel}>{texts?.signed_in_as || "Signed in as"}</p>
                <p className={styles.userValue}>{currentUser?.email || texts?.unknown_user || "unknown"}</p>
            </div>

            <nav className={styles.nav} aria-label={texts?.dashboard_tabs_aria || "Dashboard tabs"}>
                {tabs.map((tab) => (
                    <button
                        key={tab.id}
                        type="button"
                        className={`${styles.navButton} ${activeTab === tab.id ? styles.navButtonActive : ""}`}
                        onClick={() => onTabChange(tab.id)}
                    >
                        {tab.label}
                    </button>
                ))}
            </nav>

            <div className={styles.sidebarFooter}>
                <button
                    type="button"
                    className={styles.iconButton}
                    onClick={onThemeToggle}
                    aria-label={
                        theme === "dark"
                            ? texts?.switch_to_light_mode || "Switch to light mode"
                            : texts?.switch_to_dark_mode || "Switch to dark mode"
                    }
                    title={theme === "dark" ? texts?.light_mode || "Light mode" : texts?.dark_mode || "Dark mode"}
                >
                    <ThemeIcon isDarkMode={theme === "dark"} />
                </button>

                <button
                    type="button"
                    className={styles.iconButton}
                    onClick={onGoHome}
                    aria-label={texts?.go_to_home || "Go to home"}
                    title={texts?.home || "Home"}
                >
                    <HomeIcon />
                </button>

                <button
                    type="button"
                    className={`${styles.iconButton} ${styles.signOutButton}`}
                    onClick={onSignOut}
                    aria-label={texts?.sign_out || "Sign out"}
                    title={texts?.sign_out || "Sign out"}
                >
                    <SignOutIcon />
                </button>
            </div>
        </aside>
    );
}
