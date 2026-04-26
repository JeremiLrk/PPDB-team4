import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { notify } from "@/hooks/useNotify.js"

export function useRegister(setUser) {
    const [email, setEmail] = useState("")
    const [password, setPassword] = useState("")
    const [firstName, setFirstName] = useState("")
    const [lastName, setLastName] = useState("")
    const [dateOfBirth, setDateOfBirth] = useState("")
    const navigate = useNavigate()

    const handleSubmit = async (e) => {
        e.preventDefault()

        try {
            const response = await fetch("/api/signup", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                credentials: "include",
                body: JSON.stringify({
                    email: email.toLowerCase(),
                    password,
                    firstName,
                    lastName,
                    dateOfBirth,
                }),
            })

            const data = await response.json()

            if (!response.ok) {
                throw new Error(data?.message || "Registratie mislukt")
            }

            setUser(null)

            notify.success(
                data?.message ||
                    "Registratie gelukt. Controleer je e-mail om je account te verifiëren.",
            )

            navigate("/login")
        } catch (err) {
            console.error(err.message || "Registratie mislukt")
            notify.error(err.message || "Registratie mislukt")
        }
    }

    return {
        email,
        setEmail,
        password,
        setPassword,
        firstName,
        setFirstName,
        lastName,
        setLastName,
        dateOfBirth,
        setDateOfBirth,
        handleSubmit,
    }
}
