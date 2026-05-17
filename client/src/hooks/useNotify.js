// Shared hook for useNotify.

import toast from "react-hot-toast"

export const notify = {
    success(message) {
        /*
         Shows a success toast when a message is present.
        */
        if (message) {
            toast.success(message)
        }
    },
    error(message) {
        /*
         Shows an error toast when a message is present.
        */
        if (message) {
            toast.error(message)
        }
    },
}
