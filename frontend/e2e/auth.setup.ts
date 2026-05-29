import { test as setup } from "@playwright/test";
import path from "path";

const authFile = path.join(__dirname, "../.auth/user.json");

setup("authenticate", async ({ page, request }) => {
  // Register a fresh test user via API
  const email = `test-${Date.now()}@idkit.io`;
  const password = "TestPassword123!";
  const registerRes = await request.post("/api/v1/auth/register", {
    data: { email, password, full_name: "Test User" },
  });
  if (registerRes.ok()) {
    const { access_token } = await registerRes.json();
    // Visit the app root, then inject token into localStorage so the page sends Bearer headers
    await page.goto("/");
    await page.evaluate((token) => {
      localStorage.setItem("token", token);
      localStorage.setItem("access_token", token);
    }, access_token);
    // Save authenticated state (cookies + localStorage)
    await page.context().storageState({ path: authFile });
  } else {
    // Fall back: save unauthenticated state but don't crash
    await page.goto("/");
    await page.context().storageState({ path: authFile });
  }
});
