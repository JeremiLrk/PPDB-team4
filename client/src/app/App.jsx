// Top-level app shell and route composition.

import { useEffect, useState } from "react"
import { useLocation } from "react-router-dom"
import { Toaster } from "react-hot-toast"
import Background_Glow from "@/components/Background_Glow.jsx"
import Header from "@/components/Header.jsx"
import AppRoutes from "@/app/AppRoutes.jsx"
import { useLang } from "@/hooks/common/useLang.js"
import { LangContext } from "@/context/useLangContext.jsx"
import { CurrentUserProvider } from "@/context/useCurrentUserContext.jsx"
import { ThemeContext } from "@/context/useThemeContext.jsx"

const THEME_KEY = "netrank_theme"

function App() {
    const location = useLocation()
    const isDashboardRoute = location.pathname.startsWith("/dashboard")
    /*
     Owns the top-level shell state for theme, language, auth, and status.
    */
    const [status, setStatus] = useState({ state: "loading", msg: "" })
    const [lang, setLang] = useLang("en")
    const [currentUser, setCurrentUser] = useState(null)
    const [theme, setTheme] = useState(() => localStorage.getItem(THEME_KEY) || "dark")

    function toggleTheme() {
        /*
         Flips the global theme used by the entire app.
        */
        setTheme(t => t === "dark" ? "light" : "dark")
    }

    useEffect(() => {
        localStorage.setItem(THEME_KEY, theme)
        const html = document.documentElement
        if (theme === "light") {
            html.classList.add("light")
            html.classList.remove("dark")
        } else {
            html.classList.remove("light")
            html.classList.add("dark")
        }
    }, [theme])

    useEffect(() => {
        let alive = true

        async function loadCurrentUser() {
            /*
             Loads the current session user once on startup.
            */
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
                setCurrentUser(data?.account ?? null)
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
            /*
             Verifies that the backend and database are reachable.
            */
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

    const isLight = theme === "light"
    const wrapperClass = isDashboardRoute
        ? "min-h-screen overflow-x-hidden"
        : isLight
            ? "min-h-screen overflow-x-hidden bg-slate-100 text-slate-900"
            : "min-h-screen overflow-x-hidden bg-slate-950 text-slate-100"
    const mainClass = isDashboardRoute
        ? "relative z-10 min-h-screen p-0"
        : "relative z-10 flex flex-col min-h-[calc(100vh-80px)] px-4 py-4 sm:px-6 sm:py-6"

    return (
        <ThemeContext.Provider value={{ theme, toggleTheme }}>
            <div className={wrapperClass}>
                <CurrentUserProvider>
                    <LangContext.Provider value={{ lang, setLang }}>
                        {!isDashboardRoute ? <Background_Glow /> : null}
                        {!isDashboardRoute ? <Header status={status} /> : null}
                        <main className={mainClass}>
                            <AppRoutes />
                        </main>
                        <Toaster position="top-center" />
                    </LangContext.Provider>
                </CurrentUserProvider>
            </div>
        </ThemeContext.Provider>
    )
}

export default App
