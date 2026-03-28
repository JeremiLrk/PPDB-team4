import { useState } from "react"; // Vergeet useState niet toe te voegen!
import { useNavigate } from "react-router-dom";
import styles from "@/style/Clubs.module.css";
import useClubs from "@/hooks/useClubs";

function Clubs() {
    const navigate = useNavigate();
    const { clubs, loading, error } = useClubs();

    // Nieuwe state voor het formulier
    const [newClubName, setNewClubName] = useState("");
    const [isCreating, setIsCreating] = useState(false);
    const [createError, setCreateError] = useState("");

    // Functie om de club naar de backend te sturen
    const handleCreateClub = async (e) => {
        e.preventDefault(); // Voorkom dat de pagina herlaadt
        setIsCreating(true);
        setCreateError("");

        try {
            const response = await fetch('/api/clubs', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: newClubName }),
            });

            if (response.ok) {
                const data = await response.json();
                // Succes! Navigeer de kersverse manager direct naar zijn nieuwe club:
                navigate(`/clubs/${data.club.id}`);
            } else {
                const errData = await response.json();
                setCreateError(errData.message || "Fout bij aanmaken club.");
            }
        } catch (err) {
            setCreateError("Netwerkfout, kan de server niet bereiken.");
        } finally {
            setIsCreating(false);
        }
    };

    return (
        <section className={styles.container}>
            <h2 className={styles.title}>All Clubs</h2>
            <p className={styles.subtitle}>
                Kies een club om de club-homepage te openen, of start je eigen club!
            </p>

            {/* --- NIEUW: Formulier om club aan te maken --- */}
            {/* Ik heb wat inline styles toegevoegd zodat het er redelijk uitziet, 
                voel je vrij om dit naar Clubs.module.css te verplaatsen! */}
            <form 
                onSubmit={handleCreateClub} 
                style={{ marginBottom: "2rem", padding: "1.5rem", backgroundColor: "rgba(255,255,255,0.05)", borderRadius: "8px" }}
            >
                <h3 style={{ marginTop: 0, marginBottom: "1rem" }}>Nieuwe club oprichten</h3>
                <div style={{ display: "flex", gap: "10px" }}>
                    <input 
                        type="text" 
                        placeholder="Naam van jouw club..." 
                        value={newClubName}
                        onChange={(e) => setNewClubName(e.target.value)}
                        required
                        style={{ padding: "10px", borderRadius: "6px", flex: 1, border: "none" }}
                    />
                    <button 
                        type="submit" 
                        disabled={isCreating} 
                        style={{ padding: "10px 20px", cursor: "pointer", borderRadius: "6px", border: "none", backgroundColor: "#4f46e5", color: "white", fontWeight: "bold" }}
                    >
                        {isCreating ? "Bezig..." : "Aanmaken & Beheren"}
                    </button>
                </div>
                {createError && <p className={styles.error} style={{ marginTop: "10px" }}>{createError}</p>}
            </form>
            {/* ------------------------------------------- */}

            {loading && <p className={styles.info}>Clubs laden...</p>}
            {error && <p className={styles.error}>{error}</p>}

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