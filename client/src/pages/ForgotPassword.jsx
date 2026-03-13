import { Link } from "react-router-dom"
import styles from "@/style/ForgotPassword.module.css"
import { useState } from "react"
import { toast } from "react-hot-toast"

const ForgotPassword = () => {
    const [email, setEmail] = useState("")

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
                throw new Error(data?.message || "Password reset failed")
            }

            toast.success("Check your inbox for the password reset link.")
        } catch (err) {
            console.error(err.message || "Password reset failed")
            toast.error(err.message || "Password reset failed")
        }
    }

    return (
        <div className={styles.forgotContainer}>
            <div className={styles.forgotCard}>
                <h1 className={styles.forgotTitle}>Forgot your password</h1>
                <p className={styles.forgotSubtitle}>
                    Enter your email and we&apos;ll send you a reset link.
                </p>

                <form className={styles.forgotForm} onSubmit={handleSubmit}>
                    <div className={styles.forgotFormGroup}>
                        <label
                            htmlFor="forgot-email"
                            className={styles.forgotLabel}
                        >
                            Email
                        </label>
                        <input
                            id="forgot-email"
                            type="email"
                            placeholder="Enter your email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            className={styles.forgotInput}
                        />
                    </div>

                    <button type="submit" className={styles.forgotButton}>
                        Send reset link
                    </button>
                </form>

                <p className={styles.forgotText}>
                    Remembered your password?{" "}
                    <Link to="/login" className={styles.forgotLink}>
                        Back to login
                    </Link>
                </p>
            </div>
        </div>
    )
}

export default ForgotPassword
