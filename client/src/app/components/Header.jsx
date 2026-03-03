import { useNavigate } from "react-router-dom";
import Badge from "./Badge";
import styles from "@/style/Header.module.css";

export default function Header({ status, user }) {
    const navigate = useNavigate();

    return (
        <header className={styles.header}>
            <div className={styles.headerInner}>
                {/* Left: Database Status */}
                <div><Badge status={status} /></div>

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
                        <div className="relative group">
                            <button className={styles.userButton}>
                                {user.name || "User"} ▾
                            </button>

                            {/* Dropdown Menu */}
                            <div className={styles.userDropdown}>
                                <ul className="flex flex-col p-2">
                                    <li>
                                        <button
                                            className={styles.userDropdownItem}
                                            onClick={() => console.log("Go to profile")}
                                        >
                                            Profile
                                        </button>
                                    </li>
                                    <li>
                                        <button
                                            className={styles.userDropdownItem}
                                            onClick={() => console.log("Logout")}
                                        >
                                            Logout
                                        </button>
                                    </li>
                                </ul>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </header>
    );
}