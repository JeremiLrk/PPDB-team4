import { useState } from "react";
import { useNavigate } from "react-router-dom";

export function useLogin(setUser) {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            const response = await fetch("/api/login", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email: email.toLowerCase(), password }),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data?.message || "Login failed");
            }


            setUser(data.user);
            localStorage.setItem("currentUser", JSON.stringify(data.user));


            navigate("/");
        } catch (err) {
            console.error(err.message || "Login failed");
            alert(err.message || "Login failed");
        }
    };

    return { email, setEmail, password, setPassword, handleSubmit };
}