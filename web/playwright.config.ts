import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "tests",
  use: {
    baseURL: "http://127.0.0.1:4173/lidcheck/",
    viewport: { width: 390, height: 844 },
  },
  webServer: {
    command: "npm run preview -- --port 4173",
    url: "http://127.0.0.1:4173/lidcheck/",
    reuseExistingServer: !process.env.CI,
  },
  reporter: "list",
});
