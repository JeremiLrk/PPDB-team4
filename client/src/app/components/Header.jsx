import { useNavigate } from "react-router-dom"
import Badge from "./Badge"
import styles from "@/style/Header.module.css"
import { useState } from "react"
import { toast } from "react-hot-toast"
import { usePageTexts } from "@/hooks/usePageTexts.js"
import { useLangContext } from "@/context/useLangContext.js"
import { useCurrentUserContext } from "@/context/useCurrentUserContext.js"

export default function Header({ status }) {
    const navigate = useNavigate()
    const [menuOpen, setMenuOpen] = useState(false)
    const { lang, setLang } = useLangContext()
    const { currentUser, setCurrentUser } = useCurrentUserContext()

    const base_texts = usePageTexts("base", lang)
    const au_texts = usePageTexts("authorization", lang)

    const handleLogout = async () => {
        try {
            const response = await fetch("/api/logout", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                credentials: "include",
            })

            const data = await response.json()

            if (!response.ok) {
                throw new Error(data?.message || "Logout failed")
            }

            setCurrentUser(null)

            toast.success("Logout successful")

            navigate("/")
        } catch (err) {
            console.error(err.message || "Logout failed")
            toast.error(err.message || "Logout failed")
        }
    }

    return (
        <header className={styles.header}>
            <div className={styles.headerInner}>
                {/* Left: Database Status */}
                <div>
                    <Badge status={status} />
                </div>

                {/* Center: Title */}
                <h1 className={styles.headerTitle}>{base_texts.net_rank}</h1>

                {/* Right: Auth Buttons / User Menu */}
                <div className={styles.headerRight}>
                    <button onClick={() => setLang("nl")}>NL</button>
                    <button onClick={() => setLang("en")}>EN</button>

                    {!currentUser ? (
                        <>
                            <button
                                onClick={() => navigate("/login")}
                                className={styles.headerButton}
                            >
                                {au_texts.log_in}
                            </button>
                            <button
                                onClick={() => navigate("/register")}
                                className={styles.headerPrimaryButton}
                            >
                                {au_texts.register}
                            </button>
                        </>
                    ) : (
                        <div
                            className="relative pb-2"
                            onMouseEnter={() => setMenuOpen(true)}
                            onMouseLeave={() => setMenuOpen(false)}
                        >
                            <button className={styles.userButton}>
                                {(currentUser?.firstName &&
                                    currentUser?.lastName &&
                                    `${currentUser.firstName} ${currentUser.lastName}`) ||
                                    au_texts.user}{" "}
                                ▾
                            </button>

                            {/* Dropdown Menu */}
                            {menuOpen && (
                                <div className="absolute right-0 mt-2 bg-white text-black rounded shadow-lg z-50">
                                    <ul className="flex flex-col p-2">
                                        <li>
                                            <button
                                                className={
                                                    styles.userDropdownItem
                                                }
                                                onClick={() =>
                                                    console.log("Go to profile")
                                                }
                                            >
                                                {au_texts.profile}
                                            </button>
                                        </li>
                                        <li>
                                            <button
                                                className={
                                                    styles.userDropdownItem
                                                }
                                                onClick={handleLogout}
                                            >
                                                {au_texts.log_out}
                                            </button>
                                        </li>
                                    </ul>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </header>
    )
}
