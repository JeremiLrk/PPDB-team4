import { Link } from "react-router-dom"
import {useLogin} from "@/hooks/useLogin.js";
import styles from "@/style/Login.module.css";

const Login = () => {
    const { email, setEmail, password, setPassword, handleSubmit } = useLogin();

    return (
        <div className={styles.loginContainer}>
            <div className={styles.loginCard}>
                <h1 className={styles.loginTitle}>Login</h1>

                <form className={styles.loginForm} onSubmit={handleSubmit}>
                    <div className={styles.loginFormGroup}>
                        <label htmlFor="login-email" className={styles.loginLabel}>Email</label>
                        <input
                            id="login-email"
                            type="email"
                            placeholder="Enter your email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            className={styles.loginInput}
                        />
                    </div>

                    <div className={styles.loginFormGroup}>
                        <label htmlFor="login-password" className={styles.loginLabel}>Password</label>
                        <input
                            id="login-password"
                            type="password"
                            placeholder="Enter your password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className={styles.loginInput}
                        />
                    </div>

                    <button type="submit" className={styles.loginButton}>Login</button>
                </form>

                <p className={styles.loginText}>
                    Don't have an account?{" "}
                    <Link to="/register" className={styles.loginLink}>Register</Link>
                </p>

                <Link to="/" className={styles.guestLink}>Continue as guest</Link>
            </div>
        </div>
    )
}

export default Login
