import styles from "@/style/common/Forms.module.css"

export function Spinner() {
    return (
        <svg
            className={styles.spinner}
            width="14" height="14"
            viewBox="0 0 14 14"
            fill="none"
            aria-hidden="true"
        >
            <circle
                cx="7" cy="7" r="5.5"
                stroke="currentColor"
                strokeWidth="2"
                strokeDasharray="22 10"
            />
        </svg>
    );
}