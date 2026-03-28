import { useState } from "react";

const INITIAL_FORM = { name: "", clubId: "", sportTypeId: "" };

/**
 * Manages the create-team form state and submission.
 * @param {{ onCreated?: (team: object) => void }} options
 */
export function useCreateTeam({ onCreated } = {}) {
    const [form, setForm]   = useState(INITIAL_FORM);
    const [step, setStep]   = useState("idle"); // idle | form | loading | success | error
    const [error, setError] = useState("");

    function openForm() {
        setForm(INITIAL_FORM);
        setError("");
        setStep("form");
    }

    function closeForm() {
        setStep("idle");
        setForm(INITIAL_FORM);
        setError("");
    }

    function updateField(field, value) {
        setForm(prev => ({ ...prev, [field]: value }));
    }

    async function submit() {
        if (!form.name.trim()) {
            setError("Team name is required.");
            return;
        }

        setStep("loading");
        setError("");

        try {
            const body = { name: form.name.trim() };
            if (form.clubId)       body.clubId       = Number(form.clubId);
            if (form.sportTypeId)  body.sportTypeId  = Number(form.sportTypeId);

            const res = await fetch("/api/teams", {
                method:      "POST",
                credentials: "include",
                headers:     { "Content-Type": "application/json" },
                body:        JSON.stringify(body),
            });

            const data = await res.json();

            if (!res.ok) {
                setError(data?.message || "Something went wrong.");
                setStep("form");
                return;
            }

            setStep("success");
            onCreated?.(data.team);

            // Auto-close after success flash
            setTimeout(closeForm, 1400);

        } catch {
            setError("Network error. Please try again.");
            setStep("form");
        }
    }

    return {
        form,
        step,
        error,
        openForm,
        closeForm,
        updateField,
        submit,
        isOpen:    step !== "idle",
        isLoading: step === "loading",
        isSuccess: step === "success",
    };
}
