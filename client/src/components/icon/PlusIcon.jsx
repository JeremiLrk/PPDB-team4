// Icon component for PlusIcon.

export function PlusIcon({ rotated }) {
    /*
     Renders the plus icon used by expandable buttons.
    */
    return (
        <svg
            width="13" height="13"
            viewBox="0 0 13 13"
            fill="none"
            aria-hidden="true"
            style={{
                transition: "transform 0.22s ease",
                transform: rotated ? "rotate(45deg)" : "rotate(0deg)",
                flexShrink: 0,
            }}
        >
            <path d="M6.5 1v11M1 6.5h11" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
        </svg>
    );
}
