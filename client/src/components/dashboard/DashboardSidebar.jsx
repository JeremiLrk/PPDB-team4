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

    return (
        <aside className={styles.sidebar}>
            <div className={styles.brand}>NetRank</div>

            <p className={styles.userValue}>
                {loadingUser
                    ? "Loading..."
                    : currentUser?.email || texts?.unknown_user || "unknown"}
            </p>
            <nav className={navStyles.nav} aria-label={texts?.dashboard_tabs_aria || "Dashboard tabs"}>
                {tabs.map((tab) => (
                    <button
                        key={tab.id}
                        type="button"
                        className={`${navStyles.navButton} ${activeTab === tab.id ? btnStyles.navButtonActive : ""}`}
                        onClick={() => onTabChange(tab.id)}
                    >
                        {tab.label}
                    </button>
                ))}
            </nav>

            <div className={styles.sidebarFooter}>
                <button
                    type="button"
                    className={btnStyles.iconButton}
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
                    className={btnStyles.iconButton}
                    onClick={onGoHome}
                    aria-label={texts?.go_to_home || "Go to home"}
                    title={texts?.home || "Home"}
                >
                    <HomeIcon />
                </button>

                <button
                    type="button"
                    className={`${btnStyles.iconButton} ${styles.signOutButton}`}
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
