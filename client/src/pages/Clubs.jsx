import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import styles from "@/style/Clubs.module.css";

function Clubs() {
    const navigate = useNavigate();
    const [clubs, setClubs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        let alive = true;

        async function loadClubs() {
            try {
                const response = await fetch("/api/clubs");
                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data?.message || "Kon clubs niet laden.");
                }

                if (alive) {
                    setClubs(data?.clubs || []);
                    setError("");
                }
            } catch (err) {
                if (alive) {
                    setError(err?.message || "Onbekende fout.");
                    setClubs([]);
                }
            } finally {
                if (alive) {
                    setLoading(false);
                }
            }
        }

        loadClubs();
        return () => {
            alive = false;
        };
    }, []);

    return (
        <section className={styles.container}>
            <h2 className={styles.title}>All Clubs</h2>
            <p className={styles.subtitle}>
                Kies een club om de club-homepage te openen.
            </p>

            {loading ? <p className={styles.info}>Clubs laden...</p> : null}
            {error ? <p className={styles.error}>{error}</p> : null}

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
