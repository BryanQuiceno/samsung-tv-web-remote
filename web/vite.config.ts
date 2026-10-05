import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

/** En desarrollo, las llamadas a /api van al servidor Python que ya corre. */
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: { "/api": "http://127.0.0.1:8099" },
  },
});
