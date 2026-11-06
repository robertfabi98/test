import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// In sviluppo (npm run dev) le chiamate /api vanno al backend sulla porta 8765
export default defineConfig({
  plugins: [react()],
  server: { proxy: { "/api": "http://127.0.0.1:8765" } },
  build: { outDir: "dist", emptyOutDir: true },
});
