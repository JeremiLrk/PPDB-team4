import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import Background_Glow from "@/app/components/Background_Glow.jsx";
import Header from "@/app/components/Header.jsx";
import AppRoutes from "@/app/AppRoutes.jsx";

function App() {
    const location = useLocation();
    const isDashboardRoute = location.pathname.startsWith("/dashboard");
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
                const response = await fetch("/api/health");
                const data = await response.json();

                if (!response.ok || !data?.db_connected) {
                    throw new Error(data?.msg || "Database not reachable");
                }

                if (alive) {
                    setStatus({
                        state: "ok",
                        msg: "Database connected",
                    });
                }
            } catch (error) {
                if (alive) {
                    setStatus({
                        state: "err",
                        msg: error?.message || "Connection error",
                    });
                }
            }
        }

        check();
        return () => {
            alive = false;
        };
    }, []);

    const wrapperClass = isDashboardRoute ? "min-h-screen" : "min-h-screen bg-slate-950 text-slate-100";
    const mainClass = isDashboardRoute
        ? "relative z-10 min-h-screen p-0"
        : "relative z-10 flex min-h-[calc(100vh-80px)] items-center justify-center px-6 py-5";

    return (
        <div className={wrapperClass}>
            {!isDashboardRoute ? <Background_Glow /> : null}
            {!isDashboardRoute ? <Header status={status} user={currentUser} setUser={setCurrentUser} /> : null}
            <main className={mainClass}>
                <AppRoutes currentUser={currentUser} setUser={setCurrentUser} />
            </main>
        </div>
    );
}

export default App;
