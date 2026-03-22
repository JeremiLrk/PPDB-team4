import toast from "react-hot-toast"

export const notify = {
    success(message) {
        if (message) {
            toast.success(message)
        }
    },
    error(message) {
        if (message) {
            toast.error(message)
        }
    },
}
