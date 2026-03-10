import { useEffect, useState } from "react";
import Background_Glow from "@/app/components/Background_Glow.jsx";
import Header from "@/app/components/Header.jsx";
import AppRoutes from "@/app/AppRoutes.jsx";


function App() {
    const [status, setStatus] = useState({ state: "loading", msg: "" });

    const [currentUser, setCurrentUser] = useState(null);


    useEffect(() => {
        try {
            const savedUser = localStorage.getItem("currentUser");
            if (savedUser && savedUser !== "undefined") {
                setCurrentUser(JSON.parse(savedUser));
            }
        } catch (err) {
            console.error("Failed to parse saved user:", err);
        }
    }, []);

    useEffect(() => {
        let alive = true;

        async function check() {
        try {
            // API + DB status from health endpoint
            const h = await fetch("/api/health")
            const data = await h.json()
            if (!h.ok || !data?.db_connected){
                throw new Error(data?.msg || "Database not reachable")
            }

            if (alive){
                setStatus(
                    {
                        state: "ok",
                        msg: "Database connected"
                    }
                )
            }
        } catch (e) {
            if (alive) {
                setStatus(
                    {
                        state: "err",
                        msg: e?.message || "Connection error"
                    }
                )
            }

      }
    }

    check();
    return () => {
      alive = false;
    };
  }, []);

return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
        <Background_Glow />
        <Header status={status} user={currentUser} setUser={setCurrentUser}/>
        <main className="relative z-10 flex min-h-[calc(100vh-80px)] items-center justify-center px-6">
            <AppRoutes currentUser={currentUser} setUser={setCurrentUser}/>
        </main>
    </div>
    );
}

export default App
