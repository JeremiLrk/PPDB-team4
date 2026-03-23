import { useParams, useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import styles from "@/style/Home.module.css"; // Reusing your home styles for layout
import useClub from "@/hooks/useClub";
import { useLangContext } from "@/context/useLangContext.js";
import { usePageTexts } from "@/hooks/usePageTexts.js";

function ClubSettings() {
    const { clubId } = useParams();
    const navigate = useNavigate();
    const { lang } = useLangContext();
    
    // Texts (Assuming you have a settings category or reusing base)
    const baseTexts = usePageTexts("base", lang);
    const clubHomeTexts = usePageTexts("club_home", lang);
    
    const { club, loading, error } = useClub(clubId);
    
    // Form State
    const [formData, setFormData] = useState({ name: "", description: "", city: "", sport: "" });

    useEffect(() => {
        if (club) {
            setFormData({
                name: club.name || "",
                description: club.description || "",
                city: club.city || "",
                sport: club.sport || ""
            });
        }
    }, [club]);

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleUpdate = async (e) => {
        e.preventDefault();
        // Logic to hit your API (e.g., PUT /api/clubs/clubId)
        console.log("Updating club:", formData);
    };

    if (loading) return <div className="text-center mt-20">Loading Settings...</div>;

    return (
        <div className={styles.container}>
            {/* Left Sidebar: Settings Navigation */}
            <aside className={styles.ladderAside}>
                <section className={styles.ladderContainer}>
                    <h2 className={styles.ladderContainerText}>Settings</h2>
                    <div className={styles.ladderCard}>
                        <button className={`${styles.ladderButton} bg-indigo-500/20 border-l-4 border-indigo-500`}>
                            General Info
                        </button>
                        <button className={styles.ladderButton} onClick={() => navigate(`/clubs/${clubId}`)}>
                            Go to Club Home
                        </button>
                    </div>
                </section>
            </aside>

            {/* Main Content: Edit Form */}
            <section className="flex-1 max-w-2xl mx-auto">
                <h1 className="text-4xl font-bold tracking-tight mb-8">Club Settings</h1>
                
                <form onSubmit={handleUpdate} className="space-y-6 bg-slate-900/40 p-8 rounded-2xl border border-white/10">
                    <div>
                        <label className="block text-sm font-medium text-slate-300 mb-2">Club Name</label>
                        <input
                            type="text"
                            name="name"
                            value={formData.name}
                            onChange={handleChange}
                            className="w-full bg-slate-800 border border-white/10 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                        />
                    </div>

                    <div className="flex gap-4">
                        <div className="flex-1">
                            <label className="block text-sm font-medium text-slate-300 mb-2">City</label>
                            <input
                                type="text"
                                name="city"
                                value={formData.city}
                                onChange={handleChange}
                                className="w-full bg-slate-800 border border-white/10 rounded-xl px-4 py-3"
                            />
                        </div>
                        <div className="flex-1">
                            <label className="block text-sm font-medium text-slate-300 mb-2">Sport</label>
                            <input
                                type="text"
                                name="sport"
                                value={formData.sport}
                                onChange={handleChange}
                                className="w-full bg-slate-800 border border-white/10 rounded-xl px-4 py-3"
                            />
                        </div>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-slate-300 mb-2">Description</label>
                        <textarea
                            name="description"
                            value={formData.description}
                            onChange={handleChange}
                            rows="4"
                            className="w-full bg-slate-800 border border-white/10 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                        />
                    </div>

                    <div className="pt-4 border-t border-white/10">
                        <button
                            type="submit"
                            className="w-full rounded-xl bg-indigo-500 px-6 py-3 font-semibold transition hover:bg-indigo-400"
                        >
                            Save Changes
                        </button>
                    </div>
                </form>

                {/* Danger Zone */}
                <div className="mt-12 p-8 rounded-2xl border border-red-500/20 bg-red-500/5">
                    <p className="text-red-500 font-bold mb-2">
                        Deleting this club will remove all ladders, players, and historical data.
                    </p>
                    <button className="text-red-500 border border-red-500/30 px-4 py-2 rounded-lg hover:bg-red-500/10 transition">
                        Delete Club
                    </button>
                </div>
            </section>

            {/* Empty right aside to maintain your Home.module.css layout balance if needed */}
            <aside className={styles.scoreboardAside}></aside>
        </div>
    );
}

export default ClubSettings;