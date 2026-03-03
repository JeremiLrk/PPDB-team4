import { useState } from "react";
import { useNavigate } from "react-router-dom";

export function useRegister() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();

        try {
            const response = await fetch("/api/signup", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email: email.toLowerCase(), password }),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data?.message || "Registration failed");
            }

            navigate("/login");
        } catch (err) {
            console.error(err.message || "Registration failed");
        }
    };

    return { email, setEmail, password, setPassword, handleSubmit };
}