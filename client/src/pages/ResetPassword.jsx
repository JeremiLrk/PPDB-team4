import au_styles from "@/style/Authorization.module.css"
import { useState } from "react"
import { notify } from "@/hooks/useNotify.js"
import { useParams, useNavigate } from "react-router-dom"
import { useLangContext } from "@/context/useLangContext.js"
import { usePageTexts } from "@/hooks/usePageTexts.js"

const ResetPassword = () => {
    const { token } = useParams()
    const [newPassword, setNewPassword] = useState("")
    const [repeatPassword, setRepeatPassword] = useState("")
    const navigate = useNavigate()
    const { lang } = useLangContext()
    const au_texts = usePageTexts("authorization", lang)

    const handleSubmit = async (e) => {
        e.preventDefault()

        try {
            if (newPassword !== repeatPassword) {
                notify.error(au_texts.passwords_do_not_match)
                return
            }

            const response = await fetch(`/api/reset-password/${token}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ password: newPassword }),
            })

            const data = await response.json()

            if (!response.ok) {
                throw new Error(data?.message || au_texts.reset_failed)
            }

            notify.success(au_texts.password_reset_success)
            navigate("/login")
        } catch (err) {
            console.error(err.message || au_texts.reset_failed)
            notify.error(err.message || au_texts.reset_failed)
        }
    }

    return (
        <div className={au_styles.container}>
            <div className={au_styles.card}>
                <h1 className={au_styles.headerTitle}>{au_texts.reset_title}</h1>
                <form className={au_styles.form} onSubmit={handleSubmit}>
                    <div className={au_styles.formGroup}>
                        <label
                            htmlFor="new-password"
                            className={au_styles.formLabel}
                        >
                            {au_texts.new_password}
                        </label>
                        <input
                            id="new-password"
                            type="password"
                            placeholder={au_texts.placeholder_new_password}
                            value={newPassword}
                            onChange={(e) => setNewPassword(e.target.value)}
                            className={au_styles.formInput}
                            required
                        />
                    </div>

                    <div className={au_styles.formGroup}>
                        <label
                            htmlFor="repeat-password"
                            className={au_styles.formLabel}
                        >
                            {au_texts.repeat_password}
                        </label>
                        <input
                            id="repeat-password"
                            type="password"
                            placeholder={au_texts.placeholder_repeat_password}
                            value={repeatPassword}
                            onChange={(e) => setRepeatPassword(e.target.value)}
                            className={au_styles.formInput}
                            required
                        />
                    </div>

                    <button type="submit" className={au_styles.formButton}>
                        {au_texts.reset_password}
                    </button>
                </form>
            </div>
        </div>
    )
}

export default ResetPassword
