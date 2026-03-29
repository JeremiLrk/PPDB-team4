/**
 * GearIcon — SVG шестерня, яка використовується як посилання на TeamSettings.
 * Виноситься в окремий модуль, щоб повторно використовуватися в TeamCard,
 * TeamDetail та будь-де ще.
 *
 * Props:
 *   size    — розмір у px (default: 18)
 *   title   — tooltip / aria-label (default: "Settings")
 *   className — додаткові CSS-класи
 *   style   — inline styles
 */
export default function GearIcon({ size = 18, title = "Settings", className = "", style }) {
    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            width={size}
            height={size}
            viewBox="0 0 24 24"
            fill="currentColor"
            aria-label={title}
            role="img"
            className={className}
            style={style}
        >
            <title>{title}</title>
            <path d="M12 15.5A3.5 3.5 0 0 1 8.5 12 3.5 3.5 0 0 1 12 8.5a3.5 3.5 0 0 1 3.5 3.5 3.5 3.5 0 0 1-3.5 3.5m7.43-2.92c.04-.34.07-.68.07-1.08s-.03-.74-.07-1.08l2.32-1.82c.21-.16.27-.46.13-.7l-2.2-3.81c-.14-.24-.42-.32-.66-.24l-2.74 1.1c-.57-.44-1.18-.8-1.85-1.07L14.5 2.42A.55.55 0 0 0 14 2h-4c-.27 0-.5.18-.54.42L9.07 5.17C8.4 5.44 7.79 5.8 7.22 6.24L4.48 5.14a.54.54 0 0 0-.66.24L1.62 9.19c-.14.24-.08.54.13.7l2.32 1.82C4.03 12.05 4 12.39 4 12.5s.03.95.07 1.08l-2.32 1.82c-.21.16-.27.46-.13.7l2.2 3.81c.14.24.42.32.66.24l2.74-1.1c.57.44 1.18.8 1.85 1.07l.38 2.75c.04.24.27.42.54.42h4c.27 0 .5-.18.54-.42l.38-2.75c.67-.27 1.28-.63 1.85-1.07l2.74 1.1c.24.08.52 0 .66-.24l2.2-3.81c.14-.24.08-.54-.13-.7l-2.32-1.82z" />
        </svg>
    );
}
