import { useEffect, useState } from "react"
import { useLocation } from "react-router-dom"
import { Toaster } from "react-hot-toast"
import Background_Glow from "@/components/Background_Glow.jsx"
import Header from "@/components/Header.jsx"
import AppRoutes from "@/app/AppRoutes.jsx"
import {LangProvider} from "@/context/useLangContext.jsx"
import { CurrentUserProvider } from "@/context/useCurrentUserContext.jsx"

function App() {

    const location = useLocation()
    const isDashboardRoute = location.pathname.startsWith("/dashboard")
    const [status, setStatus] = useState({ state: "loading", msg: "" })

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
            <CurrentUserProvider>
                <LangProvider>
                    {!isDashboardRoute ? <Background_Glow /> : null}
                    {!isDashboardRoute ? <Header status={status} /> : null}
                    <main className={mainClass}>
                        <AppRoutes />
                    </main>
                    <Toaster position="top-center" />
                </LangProvider>
            </CurrentUserProvider>
        </div>
    )
}

export default App
