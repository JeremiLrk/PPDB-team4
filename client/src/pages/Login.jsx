import { Link } from "react-router-dom"
import { useLogin } from "@/hooks/useLogin.js"
import au_styles from "@/style/Authorization.module.css"
import { useLangContext } from "@/context/useLangContext.js"
import { usePageTexts } from "@/hooks/usePageTexts.js"

const Login = ({ setUser }) => {
    const { lang } = useLangContext()
    const au_texts = usePageTexts("authorization", lang)
    const { email, setEmail, password, setPassword, handleSubmit } =
        useLogin(setUser)

    return (
        <div className={au_styles.container}>
            <div className={au_styles.card}>
                <h1 className={au_styles.headerTitle}>{au_texts.log_in}</h1>

                <form className={au_styles.form} onSubmit={handleSubmit}>
                    <div className={au_styles.formGroup}>
                        <label
                            htmlFor="login-email"
                            className={au_styles.formLabel}
                        >
                            {au_texts.email}
                        </label>
                        <input
                            id="login-email"
                            type="email"
                            placeholder={au_texts.placeholder_email}
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            className={au_styles.formInput}
                        />
                    </div>

                    <div className={au_styles.formGroup}>
                        <label
                            htmlFor="login-password"
                            className={au_styles.formLabel}
                        >
                            {au_texts.password}
                        </label>
                        <input
                            id="login-password"
                            type="password"
                            placeholder={au_texts.placeholder_password}
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className={au_styles.formInput}
                        />
                    </div>

                    <button type="submit" className={au_styles.formButton}>
                        {au_texts.log_in}
                    </button>
                </form>

                <p className={au_styles.footerText}>
                    {au_texts.no_account}{" "}
                    <Link to="/register" className={au_styles.footerLink}>
                        {au_texts.register}
                    </Link>
                </p>

                <Link to="/forgot-password" className={au_styles.footerLink}>
                    {au_texts.forgot_password}
                </Link>

                <Link to="/" className={au_styles.footerLinkGuest}>
                    {au_texts.as_guest}
                </Link>
            </div>
        </div>
    )
}

export default Login
