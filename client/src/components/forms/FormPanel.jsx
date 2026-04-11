import { useRef, useEffect} from "react";
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
    const panelRef   = useRef(null);
    const triggerRef = useRef(null);

    // Close on click outside
    useEffect(() => {
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
        if (!isOpen) return;
        function onKey(e) { if (e.key === "Escape") closePanel(); }
        document.addEventListener("keydown", onKey);
        return () => document.removeEventListener("keydown", onKey);
    }, [isOpen, closePanel]);

    const isLastStep = step === totalSteps - 1;

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

            {/* ---Dropdown Panel --------------------------------------------------- */}
            <div
                ref={panelRef}
                role="dialog"
                aria-label={ariaLabel ?? title}
                aria-modal="true"
                className={`${panelStyles.dropdownPanel} ${panelClassName ?? ""} ${isOpen ? panelStyles.dropdownPanelOpen : ""}`}
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
                <div className={panelStyles.dropdownPanel}>
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
            </div>
        </div>
    );
}
