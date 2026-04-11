import styles from "@/style/ClubSettings.module.css";
import { useParams } from "react-router-dom";
import { useClubSettings } from "@/hooks/useClubSettings";

import ClubSidebar from "@/components/club_settings/ClubSidebar.jsx";
import ClubOverview from "@/components/club_settings/ClubOverview.jsx";
import ClubGeneral from "@/components/club_settings/ClubGeneral.jsx";
import ClubLadders from "@/components/club_settings/ClubLadders.jsx";
import ClubMembers from "@/components/club_settings/ClubMembers.jsx";


function ClubSettings() {
    const { clubId } = useParams();
    const settings = useClubSettings(clubId);
    console.log("Rendering ClubGeneral with formData:", settings.formData);

    if (settings.loading) {
        return <div className={styles.loading}>Loading club...</div>;
    }

    return (
        <section className={styles.shell}>
            <ClubSidebar
                activeTab={settings.activeTab}
                onTabChange={settings.setActiveTab}
            />

            <div className={styles.settings}>

                {settings.activeTab === "overview" && (
                    <ClubOverview club={settings.club} />
                )}

                {settings.activeTab === "general" && (
                    <ClubGeneral
                        formData={settings.formData}
                        onChange={settings.handleChange}
                        onSubmit={settings.updateClub}
                        updating={settings.updating}
                        updateMessage={settings.updateMessage}
                    />
                )}

                {settings.activeTab === "ladders" && (
                    <ClubLadders
                        ladders={settings.ladders}
                        onCreate={settings.createLadder}
                        ratingFunctions={settings.ratingFunctions}
                        ruleSets={settings.ruleSets}
                    />
                )}

                {settings.activeTab === "members" && (
                    <ClubMembers
                        members={settings.members}
                        onAdd={settings.addMember}
                        onRemove={settings.removeMember}
                    />
                )}

            </div>
        </section>
    );
}

export default ClubSettings;