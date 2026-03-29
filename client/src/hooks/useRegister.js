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
                throw new Error(data?.message || "Registration failed")
            }

            setUser(data.account)

            notify.success("Registration successful")

            navigate("/")
        } catch (err) {
            console.error(err.message || "Registration failed")
            notify.error(err.message || "Registration failed")
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
