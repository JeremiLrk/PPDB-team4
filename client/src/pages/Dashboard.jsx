import styles from "@/style/Dashboard.module.css";
import { useDashboard } from "@/hooks/useDashboard.js";

function Dashboard({ currentUser }) {
    const { dashboardData, loading, error } = useDashboard();

    if (loading) {
        return <div className={styles.container}>Dashboard laden...</div>;
    }

    const roles = dashboardData?.roles || [];
    const isPlayer = roles.includes("player");
    const isClubManager = roles.includes("club_manager");
    const isAdmin = roles.includes("admin");

    return (
        <section className={styles.container}>
            <header className={styles.header}>
                <h2 className={styles.title}>Mijn Dashboard</h2>
                <p className={styles.subtitle}>
                    Ingelogd als {currentUser?.email || "onbekende gebruiker"}
                </p>
            </header>

            {error ? <p className={styles.warning}>{error}</p> : null}

            <div className={styles.grid}>
                <article className={styles.card}>
                    <h3>Account</h3>
                    <p>Basisinformatie en accountinstellingen.</p>
                </article>

                <article className={styles.card}>
                    <h3>Clubs ontdekken</h3>
                    <p>
                        TODO(team): lijst van clubs laden + knop om join request te sturen.
                    </p>
                </article>

                <article className={styles.card}>
                    <h3>Mijn aanvragen</h3>
                    <p>
                        TODO(team): status tonen van join/clubregistratie requests van de user.
                    </p>
                </article>

                {isPlayer ? (
                    <article className={styles.card}>
                        <h3>Player Zone</h3>
                        <p>
                            TODO(team): spelersfunctionaliteit (matches, ranking, beschikbaarheid).
                        </p>
                    </article>
                ) : null}

                {isClubManager ? (
                    <article className={styles.card}>
                        <h3>Club Manager Zone</h3>
                        <p>
                            TODO(team): join requests voor de club accepteren/verwerpen.
                        </p>
                    </article>
                ) : null}

                {isAdmin ? (
                    <article className={styles.card}>
                        <h3>Admin Zone</h3>
                        <p>
                            TODO(team): club-registraties reviewen en admins beheren.
                        </p>
                    </article>
                ) : null}
            </div>
        </section>
    );
}

export default Dashboard;
