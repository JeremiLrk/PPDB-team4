// Shared hook for useLogin.

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { notify } from "@/hooks/useNotify.js";

export function useLogin(setUser) {
    /*
     Owns the login form state and submit flow.
    */
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const navigate = useNavigate();

    const handleSubmit = async (event) => {
        /*
         Validates and submits the login form.
        */
        event.preventDefault();

        try {
            const response = await fetch("/api/login", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                credentials: "include",
                body: JSON.stringify({ email: email.toLowerCase(), password }),
            });

            const data = await response.json();
            if (!response.ok) {
                throw new Error(data?.message || "Inloggen mislukt");
            }

            setUser(data.account);
            notify.success("Inloggen gelukt");
            navigate("/dashboard");
        } catch (err) {
            console.error(err?.message || "Inloggen mislukt");
            notify.error(err?.message || "Inloggen mislukt");
        }
    };

    return { email, setEmail, password, setPassword, handleSubmit };
}
