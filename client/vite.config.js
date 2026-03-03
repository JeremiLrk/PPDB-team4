import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import path from "path";

import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export default defineConfig(
    {
        plugins: [react(), tailwindcss()],
        server: {
            proxy: {
                "/api": "http://127.0.0.1:5000",
            },
        },
        test: {
            environment: "jsdom",
            globals: true,
            setupFiles: "./tests/setupTests.js",
            include: ["tests/**/*.{test,spec}.{js,jsx,ts,tsx}"],
            css: true,
        },
        resolve: {
            alias: {
                '@': path.resolve(__dirname, 'src')
            }
        }
    }
);

