import styles from "@/style/Dashboard.module.css";
import { useDashboardWorkspace } from "@/hooks/useDashboardWorkspace.js";
import DashboardSidebar from "@/app/components/dashboard/DashboardSidebar.jsx";
import { CreateClubTab, OverviewTab, RequestsTab, SearchTab } from "@/app/components/dashboard/DashboardTabs.jsx";
import { useLangContext } from "@/context/useLangContext.js";
import { usePageTexts } from "@/hooks/usePageTexts.js";

function Dashboard({ currentUser, setUser }) {
    const { lang } = useLangContext();
    const dashboardTexts = usePageTexts("dashboard", lang);
    const workspace = useDashboardWorkspace(setUser, dashboardTexts);

    if (workspace.loading) {
        return <div className={styles.loading}>{dashboardTexts.loading_dashboard || "Loading dashboard..."}</div>;
    }

    return (
        <section className={`${styles.shell} ${workspace.theme === "light" ? styles.light : ""}`}>
            <DashboardSidebar
                theme={workspace.theme}
                activeTab={workspace.activeTab}
                texts={dashboardTexts}
                onTabChange={workspace.setActiveTab}
                onThemeToggle={workspace.onThemeToggle}
                onGoHome={workspace.onGoHome}
                onSignOut={workspace.onSignOut}
            />

            <div className={styles.workspace}>


                {workspace.error ? <p className={styles.warning}>{workspace.error}</p> : null}

                {workspace.activeTab === "overview" ? (
                    <OverviewTab
                        myClubs={workspace.myClubs}
                        myRequests={workspace.myRequests}
                        pendingJoinRequestClubIds={workspace.pendingJoinRequestClubIds}
                        clubCreationRequests={workspace.clubCreationRequests}
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

                {workspace.activeTab === "requests" ? (
                    <RequestsTab 
                        myRequests={workspace.myRequests} 
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
                    />
                ) : null}
            </div>
        </section>
    );
}

export default Dashboard;
