import { useState } from "react";
import { useNavigate } from "react-router-dom";

export const useLogin = (setUser) => {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();

        try {
            const response = await fetch("/api/login", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password }),
            });

            if (response.ok) {
                const data = await response.json();
                setUser(data.user);
                navigate("/dashboard"); // Redirect to the correct page
            } else {
                console.error("Login failed");
            }
        } catch (error) {
            console.error("An error occurred during login:", error);
        }
    };

    return { email, setEmail, password, setPassword, handleSubmit };
};