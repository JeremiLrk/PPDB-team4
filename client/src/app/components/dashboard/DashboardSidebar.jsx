import styles from "@/style/Dashboard.module.css";
import { DASHBOARD_TABS } from "@/app/components/dashboard/dashboardUtils.js";
import { HomeIcon, SignOutIcon, ThemeIcon } from "@/app/components/dashboard/DashboardIcons.jsx";

export default function DashboardSidebar({
    currentUser,
    theme,
    activeTab,
    onTabChange,
    onThemeToggle,
    onGoHome,
    onSignOut,
}) {
    return (
        <aside className={styles.sidebar}>
            <div className={styles.brand}>NetRank</div>

            <div className={styles.userPanel}>
                <p className={styles.userLabel}>Signed in as</p>
                <p className={styles.userValue}>{currentUser?.email || "unknown"}</p>
            </div>

            <nav className={styles.nav} aria-label="Dashboard tabs">
                {DASHBOARD_TABS.map((tab) => (
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
                    aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
                    title={theme === "dark" ? "Light mode" : "Dark mode"}
                >
                    <ThemeIcon isDarkMode={theme === "dark"} />
                </button>

                <button
                    type="button"
                    className={styles.iconButton}
                    onClick={onGoHome}
                    aria-label="Go to home"
                    title="Home"
                >
                    <HomeIcon />
                </button>

                <button
                    type="button"
                    className={`${styles.iconButton} ${styles.signOutButton}`}
                    onClick={onSignOut}
                    aria-label="Sign out"
                    title="Sign out"
                >
                    <SignOutIcon />
                </button>
            </div>
        </aside>
    );
}
