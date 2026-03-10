import { useNavigate } from "react-router-dom"
import Badge from "./Badge"
import styles from "@/style/Header.module.css"
import { useState } from "react"

export default function Header({ status, user, setUser }) {
    const navigate = useNavigate()
    const [menuOpen, setMenuOpen] = useState(false)

    const handleLogout = async () => {
        try {
            const response = await fetch("/api/logout", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
            })

            const data = await response.json()

            if (!response.ok) {
                throw new Error(data?.message || "Logout failed")
            }

            localStorage.removeItem("currentUser")
            setUser(null)
            navigate("/")
        } catch (err) {
            console.error(err.message || "Logout failed")
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
                <h1 className={styles.headerTitle}>NetRank</h1>

                {/* Right: Auth Buttons / User Menu */}
                <div className={styles.headerRight}>
                    {!user ? (
                        <>
                            <button
                                onClick={() => navigate("/login")}
                                className={styles.headerButton}
                            >
                                Login
                            </button>
                            <button
                                onClick={() => navigate("/register")}
                                className={styles.headerPrimaryButton}
                            >
                                Register
                            </button>
                        </>
                    ) : (
                        <div
                            className="relative pb-2"
                            onMouseEnter={() => setMenuOpen(true)}
                            onMouseLeave={() => setMenuOpen(false)}
                        >
                            <button className={styles.userButton}>
                                {user.name || "User"} ▾
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
                                                Profile
                                            </button>
                                        </li>
                                        <li>
                                            <button
                                                className={
                                                    styles.userDropdownItem
                                                }
                                                onClick={handleLogout}
                                            >
                                                Logout
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
