import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { toast } from "react-hot-toast"

export function useLogin(setUser) {
    const [email, setEmail] = useState("")
    const [password, setPassword] = useState("")
    const navigate = useNavigate()

    const handleSubmit = async (e) => {
        e.preventDefault()
        try {
            const response = await fetch("/api/login", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                credentials: "include",
                body: JSON.stringify({ email: email.toLowerCase(), password }),
            })

            const data = await response.json()

            if (!response.ok) {
                throw new Error(data?.message || "Login failed")
            }

            setUser(data.user)

            toast.success("Login successful")

            navigate("/")
        } catch (err) {
            console.error(err.message || "Login failed")
            toast.error(err.message || "Login failed")
        }
    }

    return { email, setEmail, password, setPassword, handleSubmit }
}
