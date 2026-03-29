import styles from "@/style/common/Forms.module.css"
export function Field({ label, children }) {
    return (
        <label className={styles.formLabel}>
            <span>{label}</span>
            {children}
        </label>
    );
}