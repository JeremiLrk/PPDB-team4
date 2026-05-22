// Team management hook for useCreateTeam.

import { useState } from "react";

const INITIAL_FORM = { name: "", clubId: "", sportTypeId: "", addSelfAsPlayer: false };

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
    /*
     Owns the create-team wizard state and submission flow.
    */
    const [form, setForm]   = useState(INITIAL_FORM);
    const [step, setStep]   = useState(-1);
    const [error, setError] = useState("");

    function openForm() {
        /*
         Opens the wizard at the first step with a clean form.
        */
        setForm(INITIAL_FORM);
        setError("");
        setStep(0);
    }

    function closeForm() {
        /*
         Closes the wizard and clears any draft values.
        */
        setStep(-1);
        setForm(INITIAL_FORM);
        setError("");
    }

    function updateField(field, value) {
        /*
         Updates one field in the create-team form.
        */
        setForm(prev => ({ ...prev, [field]: value }));
    }
    async function submit({ afterCreated } = {}) {
        /*
         Validates and submits the create-team request.
        */
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

            const team = data?.team ?? null;

            if (typeof afterCreated === "function") {
                await afterCreated(team);
            }

            await onCreated?.(team);

            setStep(1);

            // Auto-close after success flash
            setTimeout(closeForm, 1400);
            return team;

        } catch (err) {
            setError(err?.message || "Network error. Please try again.");
            setStep(0);
            return null;
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
