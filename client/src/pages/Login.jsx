import { Link } from "react-router-dom"
import {useLogin} from "@/hooks/useLogin.js";
import styles from "@/style/Login.module.css";
import {useCurrentUserContext} from "@/context/useCurrentUserContext.js";
import {usePageTexts} from "@/hooks/usePageTexts.js";
import {useLangContext} from "@/context/useLangContext.js";

const Login = () => {

    const {lang, setLang } = useLangContext();
    const au_texts = usePageTexts("authorization", lang);

    const {currentUser, setCurrentUser } = useCurrentUserContext();
    const { email, setEmail, password, setPassword, handleSubmit } = useLogin(currentUser);


    return (
        <div className={styles.loginContainer}>
            <div className={styles.loginCard}>
                <h1 className={styles.loginTitle}>{au_texts.log_in}</h1>

                <form className={styles.loginForm} onSubmit={handleSubmit}>
                    <div className={styles.loginFormGroup}>
                        <label htmlFor="login-email" className={styles.loginLabel}>{au_texts.email}</label>
                        <input
                            id="login-email"
                            type="email"
                            placeholder={au_texts.placeholder_email}
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            className={styles.loginInput}
                        />
                    </div>

                    <div className={styles.loginFormGroup}>
                        <label htmlFor="login-password" className={styles.loginLabel}>{au_texts.password}</label>
                        <input
                            id="login-password"
                            type="password"
                            placeholder={au_texts.placeholder_password}
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className={styles.loginInput}
                        />
                    </div>

                    <button type="submit" className={styles.loginButton}>{au_texts.log_in}</button>
                </form>

                <p className={styles.loginText}>
                    {au_texts.no_account}{" "}
                    <Link to="/register" className={styles.loginLink}>{au_texts.register}</Link>
                </p>

                <Link to="/" className={styles.guestLink}>{au_texts.as_guest}</Link>
            </div>
        </div>
    )
}

export default Login
