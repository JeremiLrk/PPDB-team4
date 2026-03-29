import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import styles from "@/style/Dashboard.module.css"; // We hergebruiken dashboard styles voor consistentie

function ClubManage() {
    const { clubId } = useParams();
    const navigate = useNavigate();

    // State voor nieuwe ladder
    const [ladderName, setLadderName] = useState("");
    const [ladderDesc, setLadderDesc] = useState("");
    const [sportType, setSportType] = useState("1");
    // State voor nieuwe manager
    const [managerEmail, setManagerEmail] = useState("");

    const [message, setMessage] = useState({ text: "", type: "" });

    // Functie: Ladder toevoegen
    const handleAddLadder = async (e) => {
        e.preventDefault();
        try {
            const res = await fetch(`/api/clubs/${clubId}/ladders`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ name: ladderName, description: ladderDesc, sport_type_id: parseInt(sportType) }),
            });
            if (res.ok) {
                setMessage({ text: "Ladder succesvol aangemaakt!", type: "success" });
                setLadderName(""); setLadderDesc("");
            }
        } catch (err) {
            setMessage({ text: "Fout bij aanmaken ladder", type: "error" });
        }
    };

    // Functie: Manager toevoegen
    const handleAddManager = async (e) => {
        e.preventDefault();
        try {
            const res = await fetch(`/api/clubs/${clubId}/managers`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email: managerEmail }),
            });
            if (res.ok) {
                setMessage({ text: "Manager succesvol toegevoegd!", type: "success" });
                setManagerEmail("");
            } else {
                setMessage({ text: "Gebruiker niet gevonden of al manager.", type: "error" });
            }
        } catch (err) {
            setMessage({ text: "Fout bij toevoegen manager", type: "error" });
        }
    };

    return (
        <div className={styles.container} style={{ padding: "2rem", maxWidth: "800px", margin: "0 auto" }}>
            
            <button onClick={() => navigate(-1)} style={{ marginBottom: "1rem", cursor: "pointer" }}>
                ← Terug naar Club
            </button>
            
            <h1 className="text-3xl font-bold mb-8">Clubbeheer</h1>

            {message.text && (
                <p style={{ color: message.type === "success" ? "#4ade80" : "#f87171", marginBottom: "1rem" }}>
                    {message.text}
                </p>
            )}

            <div style={{ display: "grid", gap: "2rem" }}>
                {/* Sectie 1: Nieuwe Ladder */}
                <section style={{ background: "rgba(255,255,255,0.05)", padding: "1.5rem", borderRadius: "12px" }}>
                    <h2 className="text-xl font-semibold mb-4">Nieuwe Ladder Toevoegen</h2>
                    <form onSubmit={handleAddLadder} style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                        <input 
                            type="text" placeholder="Naam (bijv. Heren Singles 2026)" 
                            value={ladderName} onChange={(e) => setLadderName(e.target.value)}
                            className="p-2 rounded bg-slate-800 border-none text-white" required
                        />
                        <textarea 
                            placeholder="Beschrijving van de ladder..." 
                            value={ladderDesc} onChange={(e) => setLadderDesc(e.target.value)}
                            className="p-2 rounded bg-slate-800 border-none text-white"
                        />
                        <select 
    value={sportType} 
    onChange={(e) => setSportType(e.target.value)}
    className="p-2 rounded bg-slate-800 border-none text-white"
>
    <option value="1">Tennis</option>
    <option value="2">Padel</option>
</select>
                        <button type="submit" className="bg-indigo-500 p-2 rounded font-bold hover:bg-indigo-400">
                            Ladder Starten
                        </button>
                    </form>
                </section>

                {/* Sectie 2: Manager Toevoegen */}
                <section style={{ background: "rgba(255,255,255,0.05)", padding: "1.5rem", borderRadius: "12px" }}>
                    <h2 className="text-xl font-semibold mb-4">Hulpmanager Toevoegen</h2>
                    <p className="text-sm text-slate-400 mb-4">Voer het e-mailadres in van de persoon die je wilt aanstellen als mede-beheerder.</p>
                    <form onSubmit={handleAddManager} style={{ display: "flex", gap: "10px" }}>
                        <input 
                            type="email" placeholder="email@voorbeeld.com" 
                            value={managerEmail} onChange={(e) => setManagerEmail(e.target.value)}
                            className="p-2 rounded bg-slate-800 border-none text-white flex-1" required
                        />
                        <button type="submit" className="bg-amber-500 p-2 rounded font-bold text-black hover:bg-amber-400">
                            Toevoegen
                        </button>
                    </form>
                </section>
            </div>
        </div>
    );
}

export default ClubManage;