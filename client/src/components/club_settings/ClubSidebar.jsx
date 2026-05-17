// Club settings UI component for ClubSidebar.

import { useNavigate, useParams } from "react-router-dom";
import { useState } from "react";
import styles from "@/style/ClubSettings.module.css";

function ClubSidebar({ activeTab, onTabChange, texts = {}, supportsRuleSets = true }) {
    const { clubId } = useParams();
    const navigate = useNavigate();
    /*
     Owns the club-settings sidebar state and mobile drawer.
    */
    const [mobileOpen, setMobileOpen] = useState(false);
    const activeLabel = ({
        general: texts.tab_general || "Algemene info",
        ladders: texts.tab_ladders || "Ladders",
        members: texts.tab_members || "Leden",
        rules: texts.tab_rules || "Wedstrijdregels",
        owners: texts.tab_owners || "Eigenaren",
        disputed: texts.tab_disputed || "Disputed matches",
    })[activeTab] || "";

    function navClass(tab) {
        /*
         Returns the active/inactive class combination for one nav button.
        */
        return `${styles.navButton} ${activeTab === tab ? styles.navButtonActive : ""}`;
    }

    function closeMobileMenu() {
        /*
         Closes the mobile drawer after navigation.
        */
        setMobileOpen(false);
    }

    function handleTabChange(tab) {
        /*
         Switches the active settings tab and closes the mobile drawer.
        */
        onTabChange(tab);
        closeMobileMenu();
    }

    function goHome() {
        /*
         Returns to the club homepage and closes the drawer.
        */
        navigate(`/clubs/${clubId}`);
        closeMobileMenu();
    }

    return (
        <aside className={styles.sidebar}>
            <div className={styles.desktopSidebar}>
                <p className={styles.brand}>{texts.sidebar_title || "Instellingen"}</p>

                <nav className={styles.nav}>
                    <button className={navClass("general")} onClick={() => onTabChange("general")}>
                        {texts.tab_general || "Algemene info"}
                    </button>
                    <button className={navClass("ladders")} onClick={() => onTabChange("ladders")}>
                        {texts.tab_ladders || "Ladders"}
                    </button>
                    <button className={navClass("members")} onClick={() => onTabChange("members")}>
                        {texts.tab_members || "Leden"}
                    </button>
                    {supportsRuleSets && (
                        <button className={navClass("rules")} onClick={() => onTabChange("rules")}>
                            {texts.tab_rules || "Wedstrijdregels"}
                        </button>
                    )}
                    <button className={navClass("owners")} onClick={() => onTabChange("owners")}>
                        {texts.tab_owners || "Eigenaren"}
                    </button>
                    <button
                        className={`${styles.navButton} ${activeTab === "disputed" ? styles.navButtonActiveDanger : ""}`}
                        onClick={() => navigate(`/clubs/${clubId}/settings/disputed`)}
                    >
                        {texts.tab_disputed || "Disputed matches"}
                    </button>
                </nav>

                <div className={styles.sidebarFooter}>
                    <button
                        className={styles.navButton}
                        style={{ width: "100%" }}
                        onClick={() => navigate(`/clubs/${clubId}`)}
                    >
                        {texts.tab_home || "Naar clubhome"}
                    </button>
                </div>
            </div>

            <div className={styles.mobileBar}>
                <span className={styles.brand}>{texts.sidebar_title || "Instellingen"}</span>
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

            {mobileOpen && (
                <div className={styles.mobileMenu}>
                    <div className={styles.mobileMenuHeader}>
                        <p className={styles.mobileActiveLabel}>
                            {texts.sidebar_title || "Instellingen"}
                        </p>
                        <p className={styles.mobileMenuUser}>
                            {activeLabel}
                        </p>
                    </div>

                    <nav className={styles.mobileMenuNav}>
                        <button className={navClass("general")} onClick={() => handleTabChange("general")}>
                            {texts.tab_general || "Algemene info"}
                        </button>
                        <button className={navClass("ladders")} onClick={() => handleTabChange("ladders")}>
                            {texts.tab_ladders || "Ladders"}
                        </button>
                        <button className={navClass("members")} onClick={() => handleTabChange("members")}>
                            {texts.tab_members || "Leden"}
                        </button>
                        {supportsRuleSets && (
                            <button className={navClass("rules")} onClick={() => handleTabChange("rules")}>
                                {texts.tab_rules || "Wedstrijdregels"}
                            </button>
                        )}
                        <button className={navClass("owners")} onClick={() => handleTabChange("owners")}>
                            {texts.tab_owners || "Eigenaren"}
                        </button>
                        <button
                            className={`${styles.navButton} ${activeTab === "disputed" ? styles.navButtonActiveDanger : ""}`}
                            onClick={() => {
                                navigate(`/clubs/${clubId}/settings/disputed`);
                                closeMobileMenu();
                            }}
                        >
                            {texts.tab_disputed || "Disputed matches"}
                        </button>
                    </nav>

                    <div className={styles.sidebarFooter}>
                        <button
                            className={styles.navButton}
                            style={{ width: "100%" }}
                            onClick={goHome}
                        >
                            {texts.tab_home || "Naar clubhome"}
                        </button>
                    </div>
                </div>
            )}
        </aside>
    );
}

export default ClubSidebar;
