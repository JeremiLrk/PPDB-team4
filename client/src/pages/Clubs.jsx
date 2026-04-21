import { useNavigate } from "react-router-dom";
import styles from "@/style/Clubs.module.css";
import commonStyles from "@/style/common/Common.module.css";
import useClubs from "@/hooks/useClubs";

function Clubs() {
    const navigate = useNavigate();
    const { clubs, loading, error } = useClubs();


    return (
        <section className={styles.container}>
            <h2 className={styles.title}>All Clubs</h2>
            <p className={styles.subtitle}>
                Kies een club om de club-homepage te openen, of start je eigen club!
            </p>
            
            {loading && <p className={commonStyles.info}>Clubs laden...</p>}
            {error && <p className={commonStyles.error}>{error}</p>}

            <div className={styles.grid}>
                {clubs.map((club) => (
                    <button
                        key={club.id}
                        onClick={() => navigate(`/clubs/${club.id}`)}
                        className={styles.clubButton}
                    >
                        <span className={styles.clubName}>{club.name}</span>
                    </button>
                ))}
            </div>
        </section>
    );
}

export default Clubs;