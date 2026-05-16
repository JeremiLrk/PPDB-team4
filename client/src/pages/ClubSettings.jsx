import styles from "@/style/ClubSettings.module.css";
import { useParams } from "react-router-dom";
import { useClubSettings } from "@/hooks/useClubSettings";
import { useLangContext } from "@/context/useLangContext.jsx";
import { usePageTexts } from "@/hooks/common/usePageTexts.js";
import { useThemeContext } from "@/context/useThemeContext.jsx";

import ClubSidebar from "@/components/club_settings/ClubSidebar.jsx";
import ClubOverview from "@/components/club_settings/ClubOverview.jsx";
import ClubGeneral from "@/components/club_settings/ClubGeneral.jsx";
import ClubLadders from "@/components/club_settings/ClubLadders.jsx";
import ClubMatchRules from "@/components/club_settings/ClubMatchRules.jsx";
import ClubMembers from "@/components/club_settings/ClubMembers.jsx";
import ClubOwners from "@/components/club_settings/ClubOwners.jsx";


function ClubSettings() {
    const { clubId } = useParams();
    const { lang } = useLangContext();
    const texts = usePageTexts("club_settings", lang);
    const settings = useClubSettings(clubId, texts);
    const { theme } = useThemeContext();
    const isLight = theme === "light";

    if (!texts.sidebar_title) {
        return <div className={styles.loading}>{texts.loading || "Club laden..."}</div>;
    }

    if (settings.loading) {
        return <div className={styles.loading}>{texts.loading || "Club laden..."}</div>;
    }

    return (
        <section className={`${styles.shell} ${isLight ? styles.light : ""}`}>
            <ClubSidebar
                activeTab={settings.activeTab}
                onTabChange={settings.setActiveTab}
                texts={texts}
            />

            <div className={styles.workspace}>

                {settings.activeTab === "overview" && (
                    <ClubOverview club={settings.club} texts={texts} />
                )}

                {settings.activeTab === "general" && (
                    <ClubGeneral
                        formData={settings.formData}
                        onChange={settings.handleChange}
                        onCitySelect={settings.handleCitySelect}
                        onSubmit={settings.updateClub}
                        updating={settings.updating}
                        updateMessage={settings.updateMessage}
                        sportTypes={settings.sportTypes}
                        handleDeleteClub={settings.deleteClub}
                        texts={texts}
                    />
                )}

                {settings.activeTab === "ladders" && (
                    <ClubLadders
                        ladders={settings.ladders}
                        onCreate={settings.createLadder}
                        ratingFunctions={settings.ratingFunctions}
                        ruleSets={settings.ruleSets}
                        eligibleTeams={settings.eligibleTeams}
                        onAddTeam={settings.addTeamToLadder}
                        texts={texts}
                    />
                )}

                {settings.activeTab === "members" && (
                    <ClubMembers
                        members={settings.members}
                        onAdd={settings.addMember}
                        onRemove={settings.removeMember}
                        texts={texts}
                    />
                )}

                {settings.activeTab === "rules" && (
                    <ClubMatchRules clubId={clubId} texts={texts} />
                )}

                {settings.activeTab === "owners" && (
                    <ClubOwners
                        owners={settings.owners}
                        onAdd={settings.addOwner}
                        onRemove={settings.removeOwner}
                        searchAccounts={settings.searchAccounts}
                        texts={texts}
                        lang={lang}
                    />
                )}

            </div>
        </section>
    );
}

export default ClubSettings;
