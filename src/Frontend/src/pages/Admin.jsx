import { useState } from "react";
import { useNavigate } from "react-router-dom";
import styles from "@/style/Home.module.css";

function Admin() {
    const navigate = useNavigate();
    
    // 1. Navigation State
    const [activeTab, setActiveTab] = useState("overview");

    // 2. Clubs State
    const [clubs, setClubs] = useState([
        { id: 1, name: "Riverside Tennis", location: "London", members: 45 },
        { id: 2, name: "Grand Padel Center", location: "Madrid", members: 112 },
    ]);

    // 3. Users State
    const [users, setUsers] = useState([
        { id: 1, name: "John Doe", email: "john@example.com", role: "Admin", club: "Global" },
        { id: 2, name: "Jane Smith", email: "jane@tennis.com", role: "User", club: "None" },
        { id: 3, name: "Mike Ross", email: "mike@padel.com", role: "Manager", club: "Riverside Tennis" },
    ]);

    // --- ACTIONS ---
    const deleteClub = (id) => {
        if(window.confirm("Are you sure you want to delete this club?")) {
            setClubs(clubs.filter(club => club.id !== id));
        }
    };

    const addClub = () => {
        const name = prompt("Enter Club Name:");
        if (name) {
            setClubs([...clubs, { id: Date.now(), name, location: "TBD", members: 0 }]);
        }
    };

    const updateUserRole = (userId, newRole) => {
        let clubName = "None";
        if (newRole === "Admin") clubName = "Global";
        if (newRole === "Manager") clubName = prompt("Assign to which club?") || "Unassigned";

        setUsers(users.map(u => 
            u.id === userId ? { ...u, role: newRole, club: clubName } : u
        ));
    };

    return (
        <div className={styles.container}>
            {/* SHARED SIDEBAR */}
            <aside className={styles.ladderAside}>
                <button 
                    onClick={() => navigate("/")}
                    className="w-full rounded-xl bg-white/5 border border-white/10 px-3 py-2 text-xs font-medium hover:bg-white/10 transition mb-6"
                >
                    ← Back to Home
                </button>
                
                <div className="px-2">
                    <h2 className="text-slate-500 text-[10px] uppercase font-bold tracking-widest mb-4">Navigation</h2>
                    <ul className="space-y-2">
                        {["overview", "clubs", "users"].map((tab) => (
                            <li 
                                key={tab}
                                onClick={() => setActiveTab(tab)}
                                className={`text-sm p-2 rounded-lg cursor-pointer transition capitalize ${
                                    activeTab === tab 
                                    ? 'bg-indigo-500/10 text-indigo-400 font-medium' 
                                    : 'text-slate-400 hover:text-white'
                                }`}
                            >
                                {tab}
                            </li>
                        ))}
                    </ul>
                </div>
            </aside>

            {/* MAIN CONTENT AREA */}
            <main className="flex-1 overflow-y-auto px-8 py-6">
                
                {/* VIEW 1: OVERVIEW */}
                {activeTab === "overview" && (
                    <>
                        <header className="mb-10">
                            <h1 className="text-3xl font-bold text-white">Admin Controls</h1>
                            <p className="text-slate-400">Global system management for NetRank.</p>
                        </header>

                        <section className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-10">
                            <button onClick={addClub} className="flex flex-col items-start p-6 rounded-2xl bg-indigo-600 hover:bg-indigo-500 transition shadow-lg text-white text-left">
                                <span className="text-2xl mb-2">🏆</span>
                                <span className="font-bold">New Club</span>
                                <span className="text-indigo-200 text-xs">Register a new organization</span>
                            </button>
                            <button onClick={() => setActiveTab("users")} className="flex flex-col items-start p-6 rounded-2xl bg-white/5 border border-white/10 hover:bg-white/10 transition text-white text-left">
                                <span className="text-2xl mb-2">👥</span>
                                <span className="font-bold">Manage Users</span>
                                <span className="text-slate-400 text-xs">Update roles and permissions</span>
                            </button>
                        </section>
                    </>
                )}

                {/* VIEW 2: CLUBS MANAGEMENT */}
                {activeTab === "clubs" && (
                    <>
                        <header className="mb-10 flex justify-between items-end">
                            <div>
                                <h1 className="text-3xl font-bold text-white">Manage Clubs</h1>
                                <p className="text-slate-400">View and moderate all registered clubs.</p>
                            </div>
                            <button 
                                onClick={addClub}
                                className="bg-indigo-600 px-4 py-2 rounded-lg text-sm font-bold hover:bg-indigo-500 text-white"
                            >
                                + Add Club
                            </button>
                        </header>

                        <section className="rounded-2xl border border-white/10 bg-white/5 overflow-hidden">
                            <table className="w-full text-left text-sm">
                                <thead className="bg-white/5 text-slate-400 uppercase text-[10px] tracking-wider">
                                    <tr>
                                        <th className="px-6 py-3">Club Name</th>
                                        <th className="px-6 py-3">Location</th>
                                        <th className="px-6 py-3">Members</th>
                                        <th className="px-6 py-3 text-right">Actions</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-white/5">
                                    {clubs.map(club => (
                                        <tr key={club.id} className="hover:bg-white/[0.02] transition text-white">
                                            <td className="px-6 py-4 font-medium">{club.name}</td>
                                            <td className="px-6 py-4 text-slate-400">{club.location}</td>
                                            <td className="px-6 py-4 text-slate-400">{club.members}</td>
                                            <td className="px-6 py-4 text-right">
                                                <button 
                                                    onClick={() => deleteClub(club.id)}
                                                    className="text-red-400 hover:text-red-300 transition text-xs font-medium"
                                                >
                                                    Delete
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </section>
                    </>
                )}

                {/* VIEW 3: USERS VIEW */}
                {activeTab === "users" && (
                    <>
                        <header className="mb-10">
                            <h1 className="text-3xl font-bold text-white">User Directory</h1>
                            <p className="text-slate-400">Manage permissions and assign club managers.</p>
                        </header>

                        <section className="rounded-2xl border border-white/10 bg-white/5 overflow-hidden">
                            <table className="w-full text-left text-sm">
                                <thead className="bg-white/5 text-slate-400 uppercase text-[10px] tracking-wider">
                                    <tr>
                                        <th className="px-6 py-3">Name</th>
                                        <th className="px-6 py-3">Role</th>
                                        <th className="px-6 py-3">Club</th>
                                        <th className="px-6 py-3 text-right">Promote / Assign</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-white/5">
                                    {users.map(user => (
                                        <tr key={user.id} className="hover:bg-white/[0.02] text-white">
                                            <td className="px-6 py-4">
                                                <div className="font-medium">{user.name}</div>
                                                <div className="text-xs text-slate-500">{user.email}</div>
                                            </td>
                                            <td className="px-6 py-4">
                                                <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                                                    user.role === 'Admin' ? 'bg-indigo-500/20 text-indigo-400' : 
                                                    user.role === 'Manager' ? 'bg-emerald-500/20 text-emerald-400' : 
                                                    'bg-slate-500/20 text-slate-400'
                                                }`}>
                                                    {user.role}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 text-slate-400">{user.club}</td>
                                            <td className="px-6 py-4 text-right">
                                                <select 
                                                    className="bg-slate-900 border border-white/10 rounded px-2 py-1 text-xs text-white focus:outline-none focus:border-indigo-500"
                                                    value={user.role}
                                                    onChange={(e) => updateUserRole(user.id, e.target.value)}
                                                >
                                                    <option value="User">Standard User</option>
                                                    <option value="Manager">Club Manager</option>
                                                    <option value="Admin">System Admin</option>
                                                </select>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </section>
                    </>
                )}
            </main>
        </div>
    );
}

export default Admin;