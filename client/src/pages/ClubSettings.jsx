import styles from "@/style/ClubSettings.module.css";
import { useParams } from "react-router-dom";
import { useClubSettings } from "@/hooks/useClubSettings";

import ClubSidebar from "@/app/components/club_settings/ClubSidebar";
import ClubOverview from "@/app/components/club_settings/ClubOverview";
import ClubGeneral from "@/app/components/club_settings/ClubGeneral";
import ClubLadders from "@/app/components/club_settings/ClubLadders";
import ClubMembers from "@/app/components/club_settings/ClubMembers";


function ClubSettings() {
    const { clubId } = useParams();
    const settings = useClubSettings(clubId);

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