import styles from "@/style/Dashboard.module.css";
import { useDashboardWorkspace } from "@/hooks/useDashboardWorkspace.js";
import DashboardSidebar from "@/app/components/dashboard/DashboardSidebar.jsx";
import { CreateClubTab, OverviewTab, RequestsTab, SearchTab } from "@/app/components/dashboard/DashboardTabs.jsx";

function Dashboard({ currentUser, setUser }) {
    const workspace = useDashboardWorkspace(setUser);

    if (workspace.loading) {
        return <div className={styles.loading}>Dashboard laden...</div>;
    }

    return (
        <section className={`${styles.shell} ${workspace.theme === "light" ? styles.light : ""}`}>
            <DashboardSidebar
                currentUser={currentUser}
                theme={workspace.theme}
                activeTab={workspace.activeTab}
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
                    />
                ) : null}

                {workspace.activeTab === "requests" ? <RequestsTab myRequests={workspace.myRequests} /> : null}

                {workspace.activeTab === "createClub" ? (
                    <CreateClubTab
                        clubRequestForm={workspace.clubRequestForm}
                        clubRequestSubmitting={workspace.clubRequestSubmitting}
                        clubRequestMessage={workspace.clubRequestMessage}
                        clubCreationRequests={workspace.clubCreationRequests}
                        onFieldChange={workspace.onClubRequestFieldChange}
                        onSubmit={workspace.onClubRequestSubmit}
                    />
                ) : null}
            </div>
        </section>
    );
}

export default Dashboard;
