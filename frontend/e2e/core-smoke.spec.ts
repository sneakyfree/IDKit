import { test, expect } from "@playwright/test";

/**
 * IDKit Core Flow Smoke Test
 *
 * Validates critical paths work end-to-end without auth.
 * Run these before deploying to verify basic functionality.
 */

const API_BASE = process.env.PLAYWRIGHT_API_URL || "http://localhost:5857";

test.describe("IDKit Core Smoke Tests (No Auth Required)", () => {
    test.describe("Health Check", () => {
        test("backend API is healthy", async ({ request }) => {
            const response = await request.get(`${API_BASE}/api/v1/health`);
            expect(response.ok()).toBeTruthy();

            const data = await response.json();
            expect(data).toHaveProperty("status", "healthy");
            expect(data).toHaveProperty("api_version", "v1");
        });
    });

    test.describe("OpenAPI Documentation", () => {
        test("swagger docs are accessible", async ({ request }) => {
            const response = await request.get(`${API_BASE}/docs`);
            expect(response.ok()).toBeTruthy();

            const text = await response.text();
            expect(text).toContain("swagger");
        });

        test("openapi.json is available", async ({ request }) => {
            const response = await request.get(`${API_BASE}/openapi.json`);
            expect(response.ok()).toBeTruthy();

            const spec = await response.json();
            expect(spec).toHaveProperty("openapi");
            expect(spec).toHaveProperty("paths");
            expect(Object.keys(spec.paths).length).toBeGreaterThan(100);
        });
    });

    test.describe("Authentication Endpoints", () => {
        test("login endpoint exists (returns 422 without body)", async ({ request }) => {
            const response = await request.post(`${API_BASE}/api/v1/auth/login`);
            // Should return 422 (validation error) without body, not 404
            expect([400, 422]).toContain(response.status());
        });

        test("protected endpoints require auth", async ({ request }) => {
            const endpoints = [
                "/api/v1/intake/progress",
                "/api/v1/agents/capabilities",
                "/api/v1/roi/summary",
                "/api/v1/payouts/balance",
            ];

            for (const endpoint of endpoints) {
                const response = await request.get(`${API_BASE}${endpoint}`);
                expect(response.status()).toBe(401);
            }
        });
    });

    test.describe("Intake Flow", () => {
        test("intake flow endpoint exists", async ({ request }) => {
            const response = await request.get(`${API_BASE}/api/v1/intake/flow`);
            // Should return 401 (requires auth), not 404
            expect(response.status()).toBe(401);
        });
    });

    test.describe("Agent Endpoints", () => {
        test("agent capabilities endpoint exists", async ({ request }) => {
            const response = await request.get(`${API_BASE}/api/v1/agents/capabilities`);
            expect(response.status()).toBe(401); // Requires auth
        });

        test("agent task submission endpoint exists", async ({ request }) => {
            const response = await request.post(`${API_BASE}/api/v1/agents/task`);
            expect([401, 422]).toContain(response.status());
        });

        test("agent pending approvals endpoint exists", async ({ request }) => {
            const response = await request.get(`${API_BASE}/api/v1/agents/pending`);
            expect(response.status()).toBe(401);
        });
    });

    test.describe("ROI Endpoints", () => {
        test("ROI calculate endpoint exists", async ({ request }) => {
            const response = await request.post(`${API_BASE}/api/v1/roi/calculate`, {
                data: { start_date: "2026-01-01", end_date: "2026-01-24" },
            });
            expect(response.status()).toBe(401);
        });

        test("ROI summary endpoint exists", async ({ request }) => {
            const response = await request.get(`${API_BASE}/api/v1/roi/summary`);
            expect(response.status()).toBe(401);
        });
    });

    test.describe("Payouts Endpoints", () => {
        test("payouts summary endpoint exists", async ({ request }) => {
            const response = await request.get(`${API_BASE}/api/v1/payouts/summary`);
            expect(response.status()).toBe(401);
        });
    });

    test.describe("Route Count Verification", () => {
        test("API has expected number of routes (400+)", async ({ request }) => {
            const response = await request.get(`${API_BASE}/openapi.json`);
            const spec = await response.json();
            const routeCount = Object.keys(spec.paths).length;

            console.log(`Total API routes: ${routeCount}`);
            expect(routeCount).toBeGreaterThanOrEqual(400);
        });
    });
});
