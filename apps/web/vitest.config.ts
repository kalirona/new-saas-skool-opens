import { defineConfig } from "vitest/config";
import path from "path";

export default defineConfig({
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./tests/setup/vitest-setup.ts"],
    include: ["tests/**/*.test.{ts,tsx}", "tests/**/*.spec.{ts,tsx}"],
    exclude: ["node_modules", ".next"],
    css: true,
    coverage: {
      provider: "v8",
      reporter: ["text", "json", "html"],
      include: [
        "components/**/*.{ts,tsx}",
        "hooks/**/*.{ts,tsx}",
        "lib/**/*.{ts,tsx}",
        "services/**/*.{ts,tsx}",
      ],
      exclude: [
        "node_modules",
        ".next",
        "tests/**",
        "**/*.d.ts",
        "**/*.config.*",
      ],
      thresholds: {
        statements: 15,
        branches: 8,
        functions: 15,
        lines: 15,
      },
    },
    reporters: ["default", "github-actions"],
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "."),
      "@components": path.resolve(__dirname, "components"),
      "@public": path.resolve(__dirname, "public"),
      "@images": path.resolve(__dirname, "public/img"),
      "@styles": path.resolve(__dirname, "styles"),
      "@services": path.resolve(__dirname, "services"),
      "@editor": path.resolve(__dirname, "components/Objects/Editor"),
      "@hooks": path.resolve(__dirname, "components/Hooks"),
      "@lib": path.resolve(__dirname, "lib"),
    },
  },
});
