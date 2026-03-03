
import { Link } from "react-router-dom"
import {useRegister} from "@/hooks/useRegister.js";
import styles from "@/style/Register.module.css";


const Register = () => {
    const { email, setEmail, password, setPassword, handleSubmit } = useRegister();

    return (
        <div className={styles.registerContainer}>
            <div className={styles.registerCard}>
                <h1 className={styles.registerTitle}>Register</h1>

                <form className={styles.registerForm} onSubmit={handleSubmit}>
                    <div className={styles.registerFormGroup}>
                        <label htmlFor="register-email" className={styles.registerLabel}>Email</label>
                        <input
                            id="register-email"
                            type="email"
                            placeholder="Enter your email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            className={styles.registerInput}
                        />
                    </div>

                    <div className={styles.registerFormGroup}>
                        <label htmlFor="register-password" className={styles.registerLabel}>Password</label>
                        <input
                            id="register-password"
                            type="password"
                            placeholder="Enter your password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className={styles.registerInput}
                        />
                    </div>

                    <button type="submit" className={styles.registerButton}>Create account</button>
                </form>

                <p className={styles.registerText}>
                    Already have an account?{" "}
                    <Link to="/login" className={styles.registerLink}>Log in</Link>
                </p>

                <Link to="/" className={styles.guestLink}>Continue as guest</Link>
            </div>
        </div>
    )
}

export default Register
