// Shared UI building block for CityAutocompleteField.

import { useEffect, useRef, useState } from "react";
import formStyles from "@/style/common/Forms.module.css";
import styles from "@/style/common/CityAutocomplete.module.css";

export default function CityAutocompleteField({
    name = "city",
    value,
    onChange,
    onSelect,
    placeholder = "Type a city",
    minLength = 2,
    disabled = false,
    required = false,
}) {
    /*
     Owns the city search input and its suggestion dropdown.
     The parent controls the raw input value; this component handles remote
     lookup, list visibility, and selecting one suggestion.
    */
    const wrapperRef = useRef(null);
    /*
     Owns the suggestion dropdown state for the city search field.
    */
    const [suggestions, setSuggestions] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [open, setOpen] = useState(false);

    useEffect(() => {
        /*
         Fetches suggestions after the user pauses typing.
        */
        const rawQuery = (value || "").trim();

        if (!open || rawQuery.length < minLength || disabled) {
            setSuggestions([]);
            setError("");
            setLoading(false);
            return undefined;
        }

        let alive = true;
        const timeoutId = window.setTimeout(async () => {
            setLoading(true);
            setError("");

            try {
                const response = await fetch(`/api/cities/search?q=${encodeURIComponent(rawQuery)}`);
                const payload = await response.json();

                if (!response.ok) {
                    throw new Error(payload?.message || "Failed to load city suggestions.");
                }

                if (alive) {
                    setSuggestions(Array.isArray(payload?.cities) ? payload.cities : []);
                }
            } catch (err) {
                if (alive) {
                    setError(err?.message || "Failed to load city suggestions.");
                    setSuggestions([]);
                }
            } finally {
                if (alive) {
                    setLoading(false);
                }
            }
        }, 250);

        return () => {
            alive = false;
            window.clearTimeout(timeoutId);
        };
    }, [value, minLength, open, disabled]);

    useEffect(() => {
        /*
         Closes the suggestion list when the user clicks outside the field.
        */
        function onPointerDown(event) {
            if (wrapperRef.current && !wrapperRef.current.contains(event.target)) {
                setOpen(false);
            }
        }

        document.addEventListener("mousedown", onPointerDown);
        return () => document.removeEventListener("mousedown", onPointerDown);
    }, []);

    function handleSelect(city) {
        /*
         Copies the chosen city into the parent form and closes the list.
        */
        onSelect?.(city);
        setSuggestions([]);
        setOpen(false);
    }

    return (
        <div ref={wrapperRef} className={styles.wrapper}>
            <input
                className={formStyles.formInput}
                type="text"
                name={name}
                value={value}
                onChange={(event) => {
                    onChange?.(event);
                    setOpen(true);
                }}
                onFocus={() => setOpen(true)}
                onBlur={() => {
                    window.setTimeout(() => setOpen(false), 120);
                }}
                placeholder={placeholder}
                disabled={disabled}
                required={required}
                autoComplete="off"
            />

            {open && (loading || error || suggestions.length > 0 || (value || "").trim().length >= minLength) ? (
                <div className={styles.suggestions} role="listbox" aria-label="City suggestions">
                    {loading && <p className={styles.hint + " " + styles.loading}>Loading suggestions…</p>}
                    {!loading && error && <p className={styles.hint + " " + styles.error}>{error}</p>}
                    {!loading && !error && suggestions.length === 0 && (value || "").trim().length >= minLength ? (
                        <p className={styles.hint}>No matching cities found.</p>
                    ) : null}
                    {!loading && !error && suggestions.map((city) => (
                        <button
                            key={`${city.label}-${city.lat}-${city.lon}`}
                            type="button"
                            className={styles.suggestionButton}
                            onMouseDown={(event) => {
                                event.preventDefault();
                                handleSelect(city);
                            }}
                        >
                            <p className={styles.suggestionCity}>{city.label}</p>
                            <p className={styles.suggestionMeta}>
                                {city.state ? `${city.state}, ` : ""}
                                {city.country}
                            </p>
                        </button>
                    ))}
                </div>
            ) : null}
        </div>
    );
}
