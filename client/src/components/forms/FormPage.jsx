/**
 * FormPage — a single page of questions in a multi-step form.
 *
 * Renders its content only when `active === true`.
 * No state of its own — all state is stored externally (in a hook or component).
 *
 * Props:
 * active {boolean} — whether to show this page
 * children {React.ReactNode} — fields, Field-components, etc.
 */
export function FormPage({ active, children }) {
    /*
     Shows one step of a multi-step form when it is active.
    */
    if (!active) return null;
    return <>{children}</>;
}
