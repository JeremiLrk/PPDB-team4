import { useEffect, useState } from "react"
import { useLocation } from "react-router-dom"
import { Toaster } from "react-hot-toast"
import Background_Glow from "@/app/components/Background_Glow.jsx"
import Header from "@/app/components/Header.jsx"
import AppRoutes from "@/app/AppRoutes.jsx"
import { useLang } from "@/hooks/useLang.js"
import { LangContext } from "@/context/useLangContext.js"
import { CurrentUserContext } from "@/context/useCurrentUserContext.js"

function App() {
    const location = useLocation()
    const isDashboardRoute = location.pathname.startsWith("/dashboard")
    const [status, setStatus] = useState({ state: "loading", msg: "" })
    const [lang, setLang] = useLang("en")
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
                    console.error("Auth check failed:", err)
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

        async function checkHealth() {
            try {
                const response = await fetch("/api/health")
                const data = await response.json()

                if (!response.ok || !data?.db_connected) {
                    throw new Error(data?.msg || "Database not reachable")
                }

                if (alive) {
                    setStatus({ state: "ok", msg: "Database connected" })
                }
            } catch (error) {
                if (alive) {
                    setStatus({
                        state: "err",
                        msg: error?.message || "Connection error",
                    })
                }
            }
        }

        checkHealth()
        return () => {
            alive = false
        }
    }, [])

    const wrapperClass = isDashboardRoute
        ? "min-h-screen"
        : "min-h-screen bg-slate-950 text-slate-100"
    const mainClass = isDashboardRoute
        ? "relative z-10 min-h-screen p-0"
        : "relative z-10 flex min-h-[calc(100vh-80px)] items-center justify-center px-6 py-5"

    return (
        <div className={wrapperClass}>
            <Toaster position="top-center" />
            <CurrentUserContext.Provider
                value={{ currentUser, setCurrentUser }}
            >
                <LangContext.Provider value={{ lang, setLang }}>
                    {!isDashboardRoute ? <Background_Glow /> : null}
                    {!isDashboardRoute ? <Header status={status} /> : null}
                    <main className={mainClass}>
                        <AppRoutes />
                    </main>
                </LangContext.Provider>
            </CurrentUserContext.Provider>
        </div>
    )
}

export default App
