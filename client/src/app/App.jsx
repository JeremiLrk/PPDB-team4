import { useEffect, useState } from "react"
import { Toaster } from "react-hot-toast"
import Background_Glow from "@/app/components/Background_Glow.jsx"
import Header from "@/app/components/Header.jsx"
import AppRoutes from "@/app/AppRoutes.jsx"

function App() {
    const [status, setStatus] = useState({ state: "loading", msg: "" })

    const [currentUser, setCurrentUser] = useState(null)

    useEffect(() => {
        let alive = true

        async function loadCurrentUser() {
            try {
                const response = await fetch("/api/me", {
                    method: "GET",
                    credentials: "include",
                })

                if (!alive) return

                if (!response.ok) {
                    setCurrentUser(null)
                    return
                }

                const data = await response.json()
                setCurrentUser(data?.user ?? null)
            } catch (err) {
                if (alive) {
                    console.error("Auth failed:", err)
                    setCurrentUser(null)
                }
            }
        }

        loadCurrentUser()
        return () => {
            alive = false
        }
    }, [])

    useEffect(() => {
        let alive = true

        async function check() {
            try {
                // API + DB status from health endpoint
                const h = await fetch("/api/health")
                const data = await h.json()
                if (!h.ok || !data?.db_connected) {
                    throw new Error(data?.msg || "Database not reachable")
                }

                if (alive) {
                    setStatus({
                        state: "ok",
                        msg: "Database connected",
                    })
                }
            } catch (e) {
                if (alive) {
                    setStatus({
                        state: "err",
                        msg: e?.message || "Connection error",
                    })
                }
            }
        }

        check()
        return () => {
            alive = false
        }
    }, [])

    return (
        <div className="min-h-screen bg-slate-950 text-slate-100">
            <Toaster
                position="top-center"
                toastOptions={{
                    duration: 3500,
                    success: { duration: 2500 },
                    style: {
                        borderRadius: "10px",
                        background: "#0f172a",
                        color: "#e2e8f0",
                        border: "1px solid #334155",
                    },
                }}
            />
            <Background_Glow />
            <Header
                status={status}
                user={currentUser}
                setUser={setCurrentUser}
            />
            <main className="relative z-10 flex min-h-[calc(100vh-80px)] items-center justify-center px-6">
                <AppRoutes currentUser={currentUser} setUser={setCurrentUser} />
            </main>
        </div>
    )
}

export default App
