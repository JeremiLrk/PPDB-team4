// Reusable component for Field.

import styles from "@/style/common/Forms.module.css"
export function Field({ label, children }) {
    /*
     Renders one labeled form field wrapper.
    */
    return (
        <label className={styles.formLabel}>
            <span>{label}</span>
            {children}
        </label>
    );
}
