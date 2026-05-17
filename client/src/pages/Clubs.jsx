// Page container for Clubs.

import { useNavigate } from "react-router-dom";
import styles from "@/style/Clubs.module.css";
import commonStyles from "@/style/common/Common.module.css";
import useClubs from "@/hooks/useClubs";
import { useSportTypes } from "@/hooks/useSportTypes";
import { useLangContext } from "@/context/useLangContext.jsx";
import { usePageTexts } from "@/hooks/common/usePageTexts.js";

function Clubs() {
  const navigate = useNavigate();
  const { lang } = useLangContext();
  const texts = usePageTexts("clubs", lang);
  const { clubs = [], loading: clubsLoading, error: clubsError } = useClubs();
  const { sportTypes = [], error: sportsError } = useSportTypes();

  const loading = clubsLoading;
  const error = clubsError;

  if (loading) {
    /*
     Shows a compact loading state while club data is fetched.
    */
    return (
      <section className={styles.container}>
        <p className={commonStyles.info}>{texts.loading || "Loading clubs..."}</p>
      </section>
    );
  }
  return (
    <section className={styles.container}>
      <h2 className={styles.title}>{texts.title || "All clubs"}</h2>
      <p className={styles.subtitle}>{texts.subtitle || "Choose a club to open the club homepage, or start your own club!"}</p>

      {error ? <p className={commonStyles.error}>{error}</p> : null}
      {sportsError ? <p className={commonStyles.error}>{sportsError}</p> : null}

      {sportTypes.length > 0 ? sportTypes.map((sport) => {
        /*
         Groups clubs by sport type when that metadata is available.
        */
        const filteredClubs = clubs.filter(c => c.sport_type_id === sport.id);
        if (filteredClubs.length === 0) return null;

        return (
          <div key={sport.id} className={styles.sportGroup}>
            <h3 className={styles.sportGroupTitle}>{sport.name}</h3>
            <div className={styles.grid}>
              {filteredClubs.map((club) => (
                <button
                  key={club.id}
                  onClick={() => navigate(`/clubs/${club.id}`)}
                  className={styles.clubButton}
                >
                  <span className={styles.clubName}>{club.name}</span>
                  <div className={styles.clubMeta}>
                    <span>{club.city || texts.unknown_city || "Unknown city"}</span>
                    <span>{club.sport || texts.sport_not_set || "Sport not set"}</span>
                  </div>
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
              <div className={styles.clubMeta}>
                <span>{club.city || texts.unknown_city || "Unknown city"}</span>
                <span>{club.sport || texts.sport_not_set || "Sport not set"}</span>
              </div>
            </button>
          ))}
        </div>
      )}
    </section>
  );
}

export default Clubs;
