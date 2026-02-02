import { test, expect } from "@playwright/test";

/**
 * API Integration Smoke Tests
 *
 * Validates that frontend pages can communicate with backend APIs.
 * These tests verify the API wiring is functional.
 */

const API_BASE = process.env.PLAYWRIGHT_API_URL || "http://localhost:8000";

test.describe("API Smoke Tests", () => {
    test.describe("Developer Portal API", () => {
        test("should list API keys from backend", async ({ request }) => {
            const response = await request.get(`${API_BASE}/api/v1/api-keys`);
            expect(response.ok()).toBeTruthy();

            const keys = await response.json();
            expect(Array.isArray(keys)).toBeTruthy();
        });

        test("should create API key", async ({ request }) => {
            const response = await request.post(`${API_BASE}/api/v1/api-keys`, {
                data: { name: "Test Key", scopes: ["read:content"] },
            });
            expect(response.ok()).toBeTruthy();

            const key = await response.json();
            expect(key).toHaveProperty("id");
            expect(key).toHaveProperty("secret");
        });
    });

    test.describe("Contracts API", () => {
        test("should list contracts from backend", async ({ request }) => {
            const response = await request.get(`${API_BASE}/api/v1/contracts`);
            expect(response.ok()).toBeTruthy();

            const contracts = await response.json();
            expect(Array.isArray(contracts)).toBeTruthy();
        });

        test("should list contract templates", async ({ request }) => {
            const response = await request.get(`${API_BASE}/api/v1/contracts/templates`);
            expect(response.ok()).toBeTruthy();

            const templates = await response.json();
            expect(Array.isArray(templates)).toBeTruthy();
        });
    });

    test.describe("Sponsorships API", () => {
        test("should list sponsorships from backend", async ({ request }) => {
            const response = await request.get(`${API_BASE}/api/v1/sponsorships`);
            expect(response.ok()).toBeTruthy();

            const sponsorships = await response.json();
            expect(Array.isArray(sponsorships)).toBeTruthy();
        });
    });

    test.describe("Collaborations API", () => {
        test("should list collaborations from backend", async ({ request }) => {
            const response = await request.get(`${API_BASE}/api/v1/collaborations`);
            expect(response.ok()).toBeTruthy();

            const collaborations = await response.json();
            expect(Array.isArray(collaborations)).toBeTruthy();
        });
    });

    test.describe("Revenue Sharing API", () => {
        test("should list revenue agreements from backend", async ({ request }) => {
            const response = await request.get(`${API_BASE}/api/v1/revenue-sharing`);
            expect(response.ok()).toBeTruthy();

            const agreements = await response.json();
            expect(Array.isArray(agreements)).toBeTruthy();
        });
    });

    test.describe("Social Listening API", () => {
        test("should list listening queries from backend", async ({ request }) => {
            const response = await request.get(`${API_BASE}/api/v1/listening/queries`);
            expect(response.ok()).toBeTruthy();

            const queries = await response.json();
            expect(Array.isArray(queries)).toBeTruthy();
        });
    });

    test.describe("Reports API", () => {
        test("should list reports from backend", async ({ request }) => {
            const response = await request.get(`${API_BASE}/api/v1/reports`);
            expect(response.ok()).toBeTruthy();

            const reports = await response.json();
            expect(Array.isArray(reports)).toBeTruthy();
        });
    });

    test.describe("Tax API", () => {
        test("should get tax info from backend", async ({ request }) => {
            const response = await request.get(`${API_BASE}/api/v1/tax`);
            expect(response.ok()).toBeTruthy();

            const taxInfo = await response.json();
            expect(taxInfo).toHaveProperty("business_type");
        });

        test("should list tax documents from backend", async ({ request }) => {
            const response = await request.get(`${API_BASE}/api/v1/tax/documents`);
            expect(response.ok()).toBeTruthy();

            const docs = await response.json();
            expect(Array.isArray(docs)).toBeTruthy();
        });
    });

    test.describe("Admin APIs", () => {
        test("should list compliance reports", async ({ request }) => {
            const response = await request.get(`${API_BASE}/api/v1/admin/compliance`);
            expect(response.ok()).toBeTruthy();

            const reports = await response.json();
            expect(Array.isArray(reports)).toBeTruthy();
        });

        test("should list backups", async ({ request }) => {
            const response = await request.get(`${API_BASE}/api/v1/admin/backups`);
            expect(response.ok()).toBeTruthy();

            const backups = await response.json();
            expect(Array.isArray(backups)).toBeTruthy();
        });
    });

    test.describe("Offline API", () => {
        test("should get offline sync status", async ({ request }) => {
            const response = await request.get(`${API_BASE}/api/v1/offline/status`);
            expect(response.ok()).toBeTruthy();

            const status = await response.json();
            expect(status).toHaveProperty("pending_actions");
            expect(status).toHaveProperty("cached_items");
        });
    });
});
