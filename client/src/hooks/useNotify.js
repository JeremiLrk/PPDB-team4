export const notify = {
    success(message) {
        if (message) console.info(message);
    },
    error(message) {
        if (message) console.error(message);
    },
};
