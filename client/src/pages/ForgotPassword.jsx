import { Link } from "react-router-dom"
import au_styles from "@/style/Authorization.module.css"
import { useState } from "react"
import { notify } from "@/hooks/useNotify.js"
import { useLangContext } from "@/context/useLangContext.jsx"
import { usePageTexts } from "@/hooks/usePageTexts.js"

const ForgotPassword = () => {
    const [email, setEmail] = useState("")
    const { lang } = useLangContext()
    const au_texts = usePageTexts("authorization", lang)

    const handleSubmit = async (e) => {
        e.preventDefault()
        try {
            const response = await fetch("/api/forgot-password", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email: email.toLowerCase() }),
            })

            const data = await response.json()

            if (!response.ok) {
                throw new Error(data?.message || au_texts.reset_failed)
            }

            notify.success(au_texts.reset_link_sent)
        } catch (err) {
            console.error(err.message || au_texts.reset_failed)
            notify.error(err.message || au_texts.reset_failed)
        }
    }

    return (
        <div className={au_styles.container}>
            <div className={au_styles.card}>
                <h1 className={au_styles.headerTitle}>{au_texts.forgot_title}</h1>
                <p className={au_styles.headerSubtitle}>
                    {au_texts.forgot_subtitle}
                </p>

                <form className={au_styles.form} onSubmit={handleSubmit}>
                    <div className={au_styles.formGroup}>
                        <label
                            htmlFor="forgot-email"
                            className={au_styles.formLabel}
                        >
                            Email
                        </label>
                        <input
                            id="forgot-email"
                            type="email"
                            placeholder={au_texts.placeholder_email}
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            className={au_styles.formInput}
                        />
                    </div>

                    <button type="submit" className={au_styles.formButton}>
                        {au_texts.send_reset_link}
                    </button>
                </form>

                <p className={au_styles.footerText}>
                    {au_texts.remembered_password}{" "}
                    <Link to="/login" className={au_styles.footerLink}>
                        {au_texts.back_to_login}
                    </Link>
                </p>
            </div>
        </div>
    )
}

export default ForgotPassword
