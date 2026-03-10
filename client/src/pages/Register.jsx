import { Link } from "react-router-dom"
import { useRegister } from "@/hooks/useRegister.js"
import styles from "@/style/Register.module.css"

const Register = ({ setUser }) => {
    const {
        email,
        setEmail,
        password,
        setPassword,
        firstName,
        setFirstName,
        lastName,
        setLastName,
        dateOfBirth,
        setDateOfBirth,
        handleSubmit,
    } = useRegister(setUser)

    return (
        <div className={styles.registerContainer}>
            <div className={styles.registerCard}>
                <h1 className={styles.registerTitle}>Register</h1>

                <form className={styles.registerForm} onSubmit={handleSubmit}>
                    <div className={styles.nameFieldsRow}>
                        <div className={styles.registerFormGroup}>
                            <label
                                htmlFor="register-firstname"
                                className={styles.registerLabel}
                            >
                                First Name
                            </label>
                            <input
                                id="register-firstname"
                                type="text"
                                placeholder="Enter your first name"
                                value={firstName}
                                onChange={(e) => setFirstName(e.target.value)}
                                className={styles.registerInput}
                            />
                        </div>

                        <div className={styles.registerFormGroup}>
                            <label
                                htmlFor="register-lastname"
                                className={styles.registerLabel}
                            >
                                Last Name
                            </label>
                            <input
                                id="register-lastname"
                                type="text"
                                placeholder="Enter your last name"
                                value={lastName}
                                onChange={(e) => setLastName(e.target.value)}
                                className={styles.registerInput}
                            />
                        </div>
                    </div>

                    <div className={styles.registerFormGroup}>
                        <label
                            htmlFor="register-dateofbirth"
                            className={styles.registerLabel}
                        >
                            Date of Birth
                        </label>
                        <input
                            id="register-dateofbirth"
                            type="date"
                            value={dateOfBirth}
                            onChange={(e) => setDateOfBirth(e.target.value)}
                            className={styles.registerInput}
                        />
                    </div>

                    <div className={styles.registerFormGroup}>
                        <label
                            htmlFor="register-email"
                            className={styles.registerLabel}
                        >
                            Email
                        </label>
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
                        <label
                            htmlFor="register-password"
                            className={styles.registerLabel}
                        >
                            Password
                        </label>
                        <input
                            id="register-password"
                            type="password"
                            placeholder="Enter your password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className={styles.registerInput}
                        />
                    </div>

                    <button type="submit" className={styles.registerButton}>
                        Create account
                    </button>
                </form>

                <p className={styles.registerText}>
                    Already have an account?{" "}
                    <Link to="/login" className={styles.registerLink}>
                        Log in
                    </Link>
                </p>

                <Link to="/" className={styles.guestLink}>
                    Continue as guest
                </Link>
            </div>
        </div>
    )
}

export default Register
