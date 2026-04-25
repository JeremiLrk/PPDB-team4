import styles from "@/style/dashboard/Dashboard.module.css";
import commonStyles from "@/style/common/Common.module.css";
import workspaceStyles from "@/style/dashboard/Workspace.module.css";


import formStyles from "@/style/common/Forms.module.css";
import { useDashboardWorkspace } from "@/hooks/useDashboardWorkspace.js";
import DashboardSidebar from "@/components/dashboard/DashboardSidebar.jsx";
import {
    AvailabilityTab,
    CreateClubTab,
    ManageClubsTab,
    OverviewTab,
    ProfileTab,
    RequestsTab,
    SearchTab,
} from "@/components/dashboard/DashboardTabs.jsx";
import { useLangContext } from "@/context/useLangContext.jsx";
import { usePageTexts } from "@/hooks/common/usePageTexts.js";
import {useCurrentUserContext} from "@/context/useCurrentUserContext.jsx";
import {TeamsTab} from "@/components/dashboard/TeamsDashboardTab.jsx";

function Dashboard() {
    const { currentUser, setCurrentUser } = useCurrentUserContext();
    const { lang } = useLangContext()
    const dashboardTexts = usePageTexts("dashboard", lang)
    const workspace = useDashboardWorkspace(setCurrentUser, dashboardTexts)

    if (workspace.loading) {
        return (
            <div className={commonStyles.loading}>
                {dashboardTexts.loading_dashboard || "Loading dashboard..."}
            </div>
        )
    }

    return (
        <section
            className={`${commonStyles.shell} ${workspace.theme === "light" ? commonStyles.light : ""}`}
        >
            <DashboardSidebar
                theme={workspace.theme}
                activeTab={workspace.activeTab}
                isClubOwner={workspace.isClubOwner}
                texts={dashboardTexts}
                onTabChange={workspace.setActiveTab}
                onThemeToggle={workspace.onThemeToggle}
                onGoHome={workspace.onGoHome}
                onSignOut={workspace.onSignOut}
            />

            <div className={workspaceStyles.workspace}>


                {workspace.error ? <p className={formStyles.warning}>{workspace.error}</p> : null}

                {workspace.activeTab === "overview" ? (
                    <OverviewTab
                        myClubs={workspace.myClubs}
                        myRequests={workspace.myRequests}
                        pendingJoinRequestClubIds={
                            workspace.pendingJoinRequestClubIds
                        }
                        clubCreationRequests={workspace.clubCreationRequests}
                        texts={dashboardTexts}
                    />
                ) : null}

                {workspace.activeTab === "profile" ? (
                    <ProfileTab
                        currentUser={currentUser}
                        setCurrentUser={setCurrentUser}
                        texts={dashboardTexts}
                    />
                ) : null}

                {workspace.activeTab === "search" ? (
                    <SearchTab
                        searchTerm={workspace.searchTerm}
                        onSearchChange={workspace.setSearchTerm}
                        discoverLoading={workspace.discoverLoading}
                        discoverError={workspace.discoverError}
                        filteredDiscoverClubs={workspace.filteredDiscoverClubs}
                        myClubIds={workspace.myClubIds}
                        pendingJoinRequestClubIds={workspace.pendingJoinRequestClubIds}
                        clubJoinrequest={workspace.clubJoinrequest}
                        texts={dashboardTexts}
                    />
                ) : null}

                {workspace.activeTab === "availability" ? (
                    <AvailabilityTab
                        availabilityBlocks={workspace.availabilityBlocks}
                        availabilityForm={workspace.availabilityForm}
                        availabilityLoading={workspace.availabilityLoading}
                        availabilitySubmitting={
                            workspace.availabilitySubmitting
                        }
                        availabilityMessage={workspace.availabilityMessage}
                        onAvailabilityFieldChange={
                            workspace.onAvailabilityFieldChange
                        }
                        onAvailabilitySubmit={workspace.onAvailabilitySubmit}
                        onAvailabilityDelete={workspace.onAvailabilityDelete}
                        texts={dashboardTexts}
                    />
                ) : null}

                {workspace.activeTab === "requests" ? (
                    <RequestsTab 
                        myRequests={workspace.myRequests} 
                        texts={dashboardTexts} 
                        />
                ) : null}

                {workspace.activeTab === "teams" ? (
                    <TeamsTab
                        texts={dashboardTexts}
                    />
                ) : null}

                {workspace.activeTab === "createClub" ? (
                    <CreateClubTab
                        clubCreaterequest={workspace.clubCreaterequest}
                        clubRequestForm={workspace.clubRequestForm}
                        clubRequestSubmitting={workspace.clubRequestSubmitting}
                        clubRequestMessage={workspace.clubRequestMessage}
                        clubCreationRequests={workspace.clubCreationRequests}
                        onFieldChange={workspace.onClubRequestFieldChange}
                        onSubmit={workspace.onClubRequestSubmit}
                        texts={dashboardTexts}
                        incomingJoinRequests={workspace.incomingJoinRequests}
                        decideJoinrequest={workspace.decideJoinrequest}
                        isClubOwner={workspace.isClubOwner}
                    />
                ) : null}

                {workspace.activeTab === "manageClubs" ? (
                    <ManageClubsTab
                        myClubs={workspace.myClubs}
                        incomingJoinRequests={workspace.incomingJoinRequests}
                        decideJoinrequest={workspace.decideJoinrequest}
                        isClubOwner={workspace.isClubOwner}
                        onGoSettings={workspace.onGoSettings}
                        texts={dashboardTexts}
                    />
                ) : null}
            </div>
        </section>
    )
}

export default Dashboard
