import styles from "@/style/ResetPassword.module.css"
import { useState } from "react"
import { toast } from "react-hot-toast"
import { useParams, useNavigate } from "react-router-dom"

const ResetPassword = () => {
    const { token } = useParams()
    const [newPassword, setNewPassword] = useState("")
    const [repeatPassword, setRepeatPassword] = useState("")
    const navigate = useNavigate()

    const handleSubmit = async (e) => {
        e.preventDefault()

        try {
            if (newPassword !== repeatPassword) {
                toast.error("Passwords do not match")
                return
            }

            const response = await fetch(`/api/reset-password/${token}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ password: newPassword }),
            })

            const data = await response.json()

            if (!response.ok) {
                throw new Error(data?.message || "Password reset failed")
            }

            toast.success("Password has been reset.")
            navigate("/login")
        } catch (err) {
            console.error(err.message || "Password reset failed")
            toast.error(err.message || "Password reset failed")
        }
    }

    return (
        <div className={styles.resetContainer}>
            <div className={styles.resetCard}>
                <h1 className={styles.resetTitle}>Reset your password</h1>
                <form className={styles.resetForm} onSubmit={handleSubmit}>
                    <div className={styles.resetFormGroup}>
                        <label
                            htmlFor="new-password"
                            className={styles.resetLabel}
                        >
                            New password
                        </label>
                        <input
                            id="new-password"
                            type="password"
                            placeholder="Enter your new password"
                            value={newPassword}
                            onChange={(e) => setNewPassword(e.target.value)}
                            className={styles.resetInput}
                            required
                        />
                    </div>

                    <div className={styles.resetFormGroup}>
                        <label
                            htmlFor="repeat-password"
                            className={styles.resetLabel}
                        >
                            Repeat password
                        </label>
                        <input
                            id="repeat-password"
                            type="password"
                            placeholder="Repeat your new password"
                            value={repeatPassword}
                            onChange={(e) => setRepeatPassword(e.target.value)}
                            className={styles.resetInput}
                            required
                        />
                    </div>

                    <button type="submit" className={styles.resetButton}>
                        Reset Password
                    </button>
                </form>
            </div>
        </div>
    )
}

export default ResetPassword
