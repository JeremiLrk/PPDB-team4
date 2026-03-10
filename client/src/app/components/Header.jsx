import { useNavigate } from "react-router-dom";
import Badge from "./Badge";
import styles from "@/style/Header.module.css";
import { useState, useRef } from "react";

export default function Header({ status, user, setUser }) {
    const navigate = useNavigate();
    const [menuOpen, setMenuOpen] = useState(false);
    const dropdownRef = useRef(null);

    const handleClickOutside = (e) => {
        if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
            setMenuOpen(false);
        }
    };

    const toggleMenu = () => {
        setMenuOpen((prev) => !prev);
    };

    // Add event listener to close dropdown when clicking outside
    useState(() => {
        document.addEventListener("mousedown", handleClickOutside);
        return () => {
            document.removeEventListener("mousedown", handleClickOutside);
        };
    }, []);

    return (
        <header className={styles.header}>
            <div className={styles.headerInner}>
                {/* Left: Database Status */}
                <div><Badge status={status} /></div>

                {/* Center: Title */}
                <h1 className={styles.headerTitle}>
                    <button onClick={() => navigate("/")}>
                        NetRank
                    </button>
                </h1>


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
                        <div className="relative" ref={dropdownRef}>
                            <button
                                className={styles.userButton}
                                onClick={toggleMenu}
                            >
                                {user.name || "User"} ▾
                            </button>

                            {/* Dropdown Menu */}
                            {menuOpen && (
                                <div
                                    className="absolute right-0 mt-2 bg-white text-black rounded shadow-lg z-50"
                                >
                                    <ul className="flex flex-col p-2">
                                        <li>
                                            <button
                                                className={styles.userDropdownItem}
                                                onMouseDown={() => navigate("/dashboard")}
                                            >
                                                Dashboard
                                            </button>
                                        </li>
                                        <li>
                                            <button
                                                className={styles.userDropdownItem}
                                                onMouseDown={() => {
                                                    localStorage.removeItem("currentUser");
                                                    setUser(null);
                                                    navigate("/");
                                                }}
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
    );
}