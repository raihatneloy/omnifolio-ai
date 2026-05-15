import { defineConfig } from "vitest/config";
import tsconfigPaths from "vitest/configs/tsconfigPaths";

export default defineConfig({
  ...tsconfigPaths(),
  test: {
    setupFiles: ["./tests/setup.ts"],
    environment: "jsdom",
  },
});