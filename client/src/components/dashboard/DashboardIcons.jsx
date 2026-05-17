// Dashboard UI component for DashboardIcons.

export function ThemeIcon({ isDarkMode }) {
    /*
     Renders the theme-toggle icon for the current mode.
    */
    if (isDarkMode) {
        return (
            <svg viewBox="0 0 24 24" aria-hidden="true">
                <path
                    d="M12 4a1 1 0 0 1 1 1v1.2a1 1 0 0 1-2 0V5a1 1 0 0 1 1-1Zm0 12.6a4.6 4.6 0 1 0 0-9.2 4.6 4.6 0 0 0 0 9.2Zm-8-5.6a1 1 0 0 1 1-1h1.2a1 1 0 0 1 0 2H5a1 1 0 0 1-1-1Zm12.8 0a1 1 0 0 1 1-1H19a1 1 0 0 1 0 2h-1.2a1 1 0 0 1-1-1ZM6.2 6.2a1 1 0 0 1 1.4 0l.9.9a1 1 0 1 1-1.4 1.4l-.9-.9a1 1 0 0 1 0-1.4Zm9.1 9.1a1 1 0 0 1 1.4 0l.9.9a1 1 0 1 1-1.4 1.4l-.9-.9a1 1 0 0 1 0-1.4ZM7.1 15.3a1 1 0 0 1 1.4 1.4l-.9.9a1 1 0 1 1-1.4-1.4l.9-.9Zm9.1-9.1a1 1 0 0 1 1.4 1.4l-.9.9a1 1 0 0 1-1.4-1.4l.9-.9ZM12 17.8a1 1 0 0 1 1 1V20a1 1 0 0 1-2 0v-1.2a1 1 0 0 1 1-1Z"
                    fill="currentColor"
                />
            </svg>
        );
    }

    return (
        <svg viewBox="0 0 24 24" aria-hidden="true">
            <path
                d="M14.7 3.4A8.9 8.9 0 1 0 20.6 15a1 1 0 0 0-1.5-1.1 6.9 6.9 0 0 1-8.7-8.7 1 1 0 0 0-1.1-1.5h-.1a8.8 8.8 0 0 1 5.5-.3Z"
                fill="currentColor"
            />
        </svg>
    );
}

export function HomeIcon() {
    /*
     Renders the home icon used in the dashboard shell.
    */
    return (
        <svg viewBox="0 0 24 24" aria-hidden="true">
            <path
                d="M12 4.5 4.5 10v8a1 1 0 0 0 1 1h4.7a1 1 0 0 0 1-1v-4.2h1.6V18a1 1 0 0 0 1 1h4.7a1 1 0 0 0 1-1v-8L12 4.5Z"
                fill="currentColor"
            />
        </svg>
    );
}

export function SignOutIcon() {
    /*
     Renders the sign-out icon used in the dashboard shell.
    */
    return (
        <svg viewBox="0 0 24 24" aria-hidden="true">
            <path
                d="M10.5 4.5a1 1 0 0 1 0 2h-4v11h4a1 1 0 1 1 0 2h-5a1 1 0 0 1-1-1v-13a1 1 0 0 1 1-1h5Zm5.8 3.6a1 1 0 0 1 1.4 0l3.6 3.7a1 1 0 0 1 0 1.4l-3.6 3.7a1 1 0 0 1-1.4-1.4l1.9-2h-6.7a1 1 0 1 1 0-2h6.7l-1.9-2a1 1 0 0 1 0-1.4Z"
                fill="currentColor"
            />
        </svg>
    );
}
