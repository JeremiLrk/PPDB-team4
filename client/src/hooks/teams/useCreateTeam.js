import { useState } from "react";

const INITIAL_FORM = { name: "", clubId: "", sportTypeId: "" };

/**
 * Manages the create-team form state and submission.
 * @param {{ onCreated?: (team: object) => void }} options
 * error - -3
 * loading - -2
 * idle - -1
 * form - 0
 * success - 1
 *
 */
export function useCreateTeam({ onCreated } = {}) {
    const [form, setForm]   = useState(INITIAL_FORM);
    const [step, setStep]   = useState(-1);
    const [error, setError] = useState("");

    function openForm() {
        setForm(INITIAL_FORM);
        setError("");
        setStep(0);
    }

    function closeForm() {
        setStep(-1);
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

        setStep(-2);
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
                setStep(0);
                return;
            }

            setStep(1);
            onCreated?.(data.team);

            // Auto-close after success flash
            setTimeout(closeForm, 1400);

        } catch {
            setError("Network error. Please try again.");
            setStep(0);
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
        isOpen:    step !== -1,
        isLoading: step === -2,
        isSuccess: step === 1,
    };
}
