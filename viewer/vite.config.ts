import react from "@vitejs/plugin-react";
import path from "path";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@seoulgaok/bim-core": path.resolve(__dirname, "../typescript/src/index.ts"),
      "@seoulgaok/bim-visualizer": path.resolve(__dirname, "../visualizer/src/index.ts"),
    },
  },
});
