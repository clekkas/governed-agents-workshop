import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Proxy /api to the backend during development so the UI and backend can run
// on separate ports without CORS friction. In single-process deployment the
// backend serves the built UI, so /api is same-origin there too.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8080",
        changeOrigin: true,
      },
    },
  },
});
