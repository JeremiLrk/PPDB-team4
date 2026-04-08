import { useEffect, useMemo, useState } from "react"
import { Link, useParams } from "react-router-dom"
import styles from "@/style/VerifyEmail.module.css"
import { useLangContext } from "@/context/useLangContext.jsx"
import { usePageTexts } from "@/hooks/common/usePageTexts.js"

const VerifyEmail = () => {
    const { token } = useParams()
    const [status, setStatus] = useState("loading")
    const { lang } = useLangContext()
    const au_texts = usePageTexts("authorization", lang)

    useEffect(() => {
        let cancelled = false

        async function verifyToken() {
            try {
                const response = await fetch(`/api/verify-email/${token}`, {
                    method: "GET",
                })

                if (!cancelled) {
                    setStatus(response.ok ? "success" : "error")
                }
            } catch {
                if (!cancelled) {
                    setStatus("error")
                }
            }
        }

        verifyToken()

        return () => {
            cancelled = true
        }
    }, [token])

    const title = useMemo(() => {
        if (status === "loading") {
            return au_texts.verify_pending || "Verifying your email"
        }
        if (status === "success") {
            return au_texts.verify_success || "Email verified successfully"
        }
        return (
            au_texts.verify_failed || "Verification link is invalid or expired"
        )
    }, [
        au_texts.verify_failed,
        au_texts.verify_pending,
        au_texts.verify_success,
        status,
    ])

    return (
        <div className={styles.verifyContainer}>
            <div className={styles.verifyCard}>
                <h1 className={styles.verifyTitle}>
                    {au_texts.verify_title || "Email verification"}
                </h1>
                <p className={styles.verifySubtitle}>{title}</p>

                <Link to="/login" className={styles.verifyLink}>
                    {au_texts.back_to_login || "Back to login"}
                </Link>
            </div>
        </div>
    )
}

export default VerifyEmail
