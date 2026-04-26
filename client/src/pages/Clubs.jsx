import { useNavigate } from "react-router-dom";
import styles from "@/style/Clubs.module.css";
import commonStyles from "@/style/common/Common.module.css";
import useClubs from "@/hooks/useClubs";
import { useSportTypes } from "@/hooks/useSportTypes";

function Clubs() {
  const navigate = useNavigate();
  const { clubs = [], loading: clubsLoading, error: clubsError } = useClubs();
  const { sportTypes = [], loading: sportsLoading, error: sportsError } = useSportTypes();

  const loading = clubsLoading;
  const error = clubsError;

  if (loading) {
    return (
      <section className={styles.container}>
        <p className={commonStyles.info}>Clubs laden...</p>
      </section>
    );
  }
  return (
    <section className={styles.container}>
      <h2 className={styles.title}>All Clubs</h2>
      <p className={styles.subtitle}>Kies een club om de club-homepage te openen, of start je eigen club!</p>

      {error ? <p className={commonStyles.error}>{error}</p> : null}
      {sportsError ? <p className={commonStyles.error}>{sportsError}</p> : null}

      {sportTypes.length > 0 ? sportTypes.map((sport) => {
        const filteredClubs = clubs.filter(c => c.sport_type_id === sport.id);
        if (filteredClubs.length === 0) return null;

        return (
          <div key={sport.id} style={{ marginTop: "1.5rem" }}>
            <h3 style={{ margin: 0, fontSize: "1.125rem", fontWeight: 600 }}>{sport.name}</h3>
            <div className={styles.grid}>
              {filteredClubs.map((club) => (
                <button
                  key={club.id}
                  onClick={() => navigate(`/clubs/${club.id}`)}
                  className={styles.clubButton}
                >
                  <span className={styles.clubName}>{club.name}</span>
                  <span>{club.city}</span>
                </button>
              ))}
            </div>
          </div>
        );
      }) : (
        <div className={styles.grid}>
          {clubs.map((club) => (
            <button
              key={club.id}
              onClick={() => navigate(`/clubs/${club.id}`)}
              className={styles.clubButton}
            >
              <span className={styles.clubName}>{club.name}</span>
              <span>{club.city}</span>
            </button>
          ))}
        </div>
      )}
    </section>
  );
}

export default Clubs;
