import { Link } from "react-router-dom"
import {useRegister} from "@/hooks/useRegister.js";
import styles from "@/style/Register.module.css";
import {useCurrentUserContext} from "@/context/useCurrentUserContext.js";
import {useLangContext} from "@/context/useLangContext.js";
import {usePageTexts} from "@/hooks/usePageTexts.js";


const Register = () => {

    const {lang, setLang } = useLangContext();
    const au_texts = usePageTexts("authorization", lang);

    const {currentUser, setCurrentUser } = useCurrentUserContext();
    const { email, setEmail, password, setPassword, handleSubmit } = useRegister(setCurrentUser);

    return (
        <div className={styles.registerContainer}>
            <div className={styles.registerCard}>
                <h1 className={styles.registerTitle}>{au_texts.register}</h1>

                <form className={styles.registerForm} onSubmit={handleSubmit}>
                    <div className={styles.registerFormGroup}>
                        <label htmlFor="register-email" className={styles.registerLabel}>{au_texts.email}</label>
                        <input
                            id="register-email"
                            type="email"
                            placeholder={au_texts.placeholder_email}
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            className={styles.registerInput}
                        />
                    </div>

                    <div className={styles.registerFormGroup}>
                        <label htmlFor="register-password" className={styles.registerLabel}>{au_texts.password}</label>
                        <input
                            id="register-password"
                            type="password"
                            placeholder={au_texts.placeholder_password}
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className={styles.registerInput}
                        />
                    </div>

                    <button type="submit" className={styles.registerButton}>{au_texts.create_account}</button>
                </form>

                <p className={styles.registerText}>
                    {au_texts.has_account}{" "}
                    <Link to="/login" className={styles.registerLink}>{au_texts.log_in}</Link>
                </p>

                <Link to="/" className={styles.guestLink}>{au_texts.as_guest}</Link>
            </div>
        </div>
    )
}

export default Register
