// Reusable component for FormPanel.

import { useRef, useEffect} from "react";
import { createPortal } from "react-dom";
import { Spinner } from "@/components/forms/Spinner.jsx";
import { SuccessIcon } from "@/components/icon/SuccessIcon.jsx";
import commonStyles from "@/style/common/Common.module.css";
import fromStyles from "@/style/common/Forms.module.css";
import panelStyles from "@/style/common/Panel.module.css";
import buttonStyles from "@/style/common/Buttons.module.css";

/**
 * FormPanel — drop-down dialog with step-by-step navigation (Back / Next / Confirm).
 *
 * Divided into two logical parts:
 * 1. Question pages — children of `<FormPage>` (rendered in panelBody)
 * 2. Navigation footer — «Back» / «Next» / «Confirm» (rendered in panelFooter)
 *
 * Props:
 * title {string} — panel title
 * triggerContent {React.ReactNode} — trigger button content
 * triggerClassName {string=} — trigger CSS class (by default styles.trigger)
 * triggerOpenClassName {string=} — additional class when open
 *
 * isOpen {boolean}
 * openPanel {() => void}
 * closePanel {() => void}
 *
 * step {number} — current page index (0-based)
 * totalSteps {number} — total number of pages
 * onNext {() => void} — go to next page
 * onBack {() => void} — go back to previous
 * onSubmit {() => void} — submit form (only on last page)
 *
 * isLoading {boolean}
 * isSuccess {boolean}
 * successLabel {string=} — text after success (default "Done!")
 * error {string|null}
 *
 * submitLabel {string=} — text of the confirmation button (default "Confirm")
 * canNext {boolean=} — whether the "Next" / "Confirm" button is active (default true)
 *
 * panelClassName {string=} — additional CSS class of the panel
 * ariaLabel {string=} — aria-label of the dialog
 *
 * children {React.ReactNode} — <FormPage> elements
 */
export function FormPanel({
    title,
    triggerContent,
    triggerClassName,
    triggerOpenClassName,
    theme,

    isOpen,
    openPanel,
    closePanel,

    step,
    totalSteps,
    onNext,
    onBack,
    onSubmit,

    isLoading = false,
    isSuccess = false,
    successLabel = "Done!",
    error = null,

    submitLabel = "Confirm",
    canNext = true,

    panelClassName,
    ariaLabel,

    children,
}) {
    /*
     Owns the shared dropdown-panel shell for multi-step forms.
     The caller supplies the content and callbacks; this component handles
     panel positioning, outside-click/escape dismissal, and footer controls.
    */
    const panelRef   = useRef(null);
    const triggerRef = useRef(null);

    // Close on click outside
    useEffect(() => {
        /*
         Closes the panel when the user clicks outside the trigger and dialog.
        */
        if (!isOpen) return;
        function onOutside(e) {
            if (
                panelRef.current   && !panelRef.current.contains(e.target) &&
                triggerRef.current && !triggerRef.current.contains(e.target)
            ) closePanel();
        }
        document.addEventListener("mousedown", onOutside);
        return () => document.removeEventListener("mousedown", onOutside);
    }, [isOpen, closePanel]);

    // Close by Escape
    useEffect(() => {
        /*
         Closes the panel when the user presses Escape.
        */
        if (!isOpen) return;
        function onKey(e) { if (e.key === "Escape") closePanel(); }
        document.addEventListener("keydown", onKey);
        return () => document.removeEventListener("keydown", onKey);
    }, [isOpen, closePanel]);

    const isLastStep = step === totalSteps - 1;
    const themeVars = theme === "light"
        ? {
            "--text-primary": "#0f172a",
            "--text-secondary": "#475569",
            "--text-heading": "#020617",
            "--surface-bg-soft": "rgba(241, 245, 249, 0.96)",
            "--surface-border": "rgba(71, 85, 105, 0.26)",
            "--muted-border": "rgba(71, 85, 105, 0.24)",
            "--input-bg": "rgba(255, 255, 255, 0.98)",
            "--input-border": "rgba(71, 85, 105, 0.38)",
            "--action-text": "#0f172a",
            "--action-bg": "linear-gradient(120deg, rgba(186, 230, 253, 0.86), rgba(153, 246, 228, 0.68))",
            "--action-border": "rgba(6, 182, 212, 0.6)",
            "--action-hover-bg": "linear-gradient(120deg, rgba(147, 197, 253, 0.78), rgba(94, 234, 212, 0.72))",
            "--action-hover-border": "rgba(8, 145, 178, 0.72)",
            "--danger-bg": "rgba(254, 226, 226, 0.92)",
            "--danger-border": "rgba(239, 68, 68, 0.42)",
            "--danger-text": "#7f1d1d",
        }
        : {
            "--text-primary": "#e2e8f0",
            "--text-secondary": "#94a3b8",
            "--text-heading": "#f8fafc",
            "--surface-bg-soft": "rgba(15, 23, 42, 0.96)",
            "--surface-border": "rgba(148, 163, 184, 0.24)",
            "--muted-border": "rgba(148, 163, 184, 0.2)",
            "--input-bg": "rgba(15, 23, 42, 0.95)",
            "--input-border": "rgba(148, 163, 184, 0.42)",
            "--action-text": "#ecfeff",
            "--action-bg": "linear-gradient(120deg, rgba(14, 116, 144, 0.45), rgba(16, 185, 129, 0.38))",
            "--action-border": "rgba(45, 212, 191, 0.62)",
            "--action-hover-bg": "linear-gradient(120deg, rgba(14, 165, 233, 0.52), rgba(20, 184, 166, 0.42))",
            "--action-hover-border": "rgba(110, 231, 183, 0.8)",
            "--danger-bg": "rgba(127, 29, 29, 0.34)",
            "--danger-border": "rgba(248, 113, 113, 0.4)",
            "--danger-text": "#fecaca",
        };

    // --- Navigation footer ----------------------------------------------------
    const navigationFooter = !isSuccess && (
        <div className={panelStyles.panelFooter}>
            {/* Back button — hidden on the first page*/}
            {step > 0 && (
                <button
                    className={buttonStyles.backBtn}
                    onClick={onBack}
                    disabled={isLoading}
                >
                    Back
                </button>
            )}

            {/* Spacer — so that "Next/Confirm" is always on the right */}
            <span className={panelStyles.panelFooterSpacer} />

            {/* "Next" or "Confirm" */}
            {isLastStep ? (
                <button
                    className={buttonStyles.submitBtn}
                    onClick={onSubmit}
                    disabled={isLoading || !canNext}
                >
                    {isLoading ? <><Spinner /> Loading…</> : submitLabel}
                </button>
            ) : (
                <button
                    className={buttonStyles.nextBtn}
                    onClick={onNext}
                    disabled={isLoading || !canNext}
                >
                    Next
                </button>
            )}
        </div>
    );

    return (
        <div className={fromStyles.wrapper}>
            {/* --- Trigger --------------------------------------------------- */}
            <button
                ref={triggerRef}
                onClick={isOpen ? closePanel : openPanel}
                className={`${triggerClassName ?? fromStyles.trigger} ${isOpen ? (triggerOpenClassName ?? fromStyles.triggerOpen) : ""}`}
                aria-expanded={isOpen}
                aria-haspopup="dialog"
            >
                {triggerContent}
            </button>

            {/* ---Dropdown Panel — rendered via portal at <body> so that
                 position:fixed is always relative to the viewport, not to any
                 ancestor that has transform/animation (e.g. .contentFade).    */}
            {createPortal(

                <div
                    ref={panelRef}
                    role="dialog"
                    aria-label={ariaLabel ?? title}
                    aria-modal="true"
                    className={`${panelStyles.dropdownPanel} ${panelClassName ?? ""} ${isOpen ? panelStyles.dropdownPanelOpen : ""}`}
                    style={themeVars}
                >
                    {/* Title */}
                    <div className={panelStyles.dropdownPanelHeader}>
                        <p className={panelStyles.dropdownPanelTitle}>{title}</p>
                        <button
                            className={buttonStyles.closeBtn}
                            onClick={closePanel}
                            aria-label="Close"
                        >
                            ×
                        </button>
                    </div>

                    {/* --- Part 1: Question Pages --------------------------- */}
                    <div className={panelStyles.panelBody}>
                        {isSuccess ? (
                            <div className={fromStyles.successBody}>
                                <SuccessIcon />
                                <p className={fromStyles.successLabel}>{successLabel}</p>
                            </div>
                        ) : (
                            <>
                                {children}
                                {error && <p className={commonStyles.error}>{error}</p>}
                            </>
                        )}
                    </div>

                    {/* --- Part 2: Footer Navigation --------------------------- */}
                    {navigationFooter}
                </div>,
                document.body
            )}
        </div>
    );
}
