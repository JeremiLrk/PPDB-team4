// Vite build and test configuration for the frontend app.

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

import { fileURLToPath } from "url";
import tailwindcss from "@tailwindcss/vite";
import i18nPlugin from "./vite-plugin-i18n.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export default defineConfig(
    {
        plugins: [react(), tailwindcss(), i18nPlugin()],
        test: {
            globals: true,
            environment: "jsdom",
            setupFiles: "./tests/setupTests.js",
        },
        server: {
            proxy: {
                "/api": {
                    target: "http://localhost:5000",
                    changeOrigin: true,
                },
            },
        },
        resolve: {
            alias: {
                '@': path.resolve(__dirname, 'src')
            }
        }
    }
);
