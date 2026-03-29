import { Link } from "react-router-dom"
import au_styles from "@/style/Authorization.module.css"
import { useState } from "react"
import { notify } from "@/hooks/useNotify.js"
import { useLangContext } from "@/context/useLangContext.js"
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
        <div className={au_styles.forgotContainer}>
            <div className={au_styles.forgotCard}>
                <h1 className={au_styles.forgotTitle}>{au_texts.forgot_title}</h1>
                <p className={au_styles.forgotSubtitle}>
                    {au_texts.forgot_subtitle}
                </p>

                <form className={au_styles.forgotForm} onSubmit={handleSubmit}>
                    <div className={au_styles.forgotFormGroup}>
                        <label
                            htmlFor="forgot-email"
                            className={au_styles.forgotLabel}
                        >
                            Email
                        </label>
                        <input
                            id="forgot-email"
                            type="email"
                            placeholder={au_texts.placeholder_email}
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            className={au_styles.forgotInput}
                        />
                    </div>

                    <button type="submit" className={au_styles.forgotButton}>
                        {au_texts.send_reset_link}
                    </button>
                </form>

                <p className={au_styles.forgotText}>
                    {au_texts.remembered_password}{" "}
                    <Link to="/login" className={au_styles.forgotLink}>
                        {au_texts.back_to_login}
                    </Link>
                </p>
            </div>
        </div>
    )
}

export default ForgotPassword
