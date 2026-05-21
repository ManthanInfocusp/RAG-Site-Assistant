import { defineConfig } from "vite";

export default defineConfig({
  build: {
    target: "es2020",
    cssCodeSplit: false,
    rollupOptions: {
      input: "src/index.ts",
      output: {
        entryFileNames: "chat.js",
        format: "iife",
        inlineDynamicImports: true,
      },
    },
  },
});
