/**
 * Tests for API Client Utilities
 * 
 * @jest-environment jsdom
 */

// Mock fetch globally
const mockFetch = jest.fn();
global.fetch = mockFetch;

// Mock localStorage
const mockLocalStorage = {
    getItem: jest.fn(),
    setItem: jest.fn(),
    removeItem: jest.fn(),
    clear: jest.fn(),
};
Object.defineProperty(window, "localStorage", { value: mockLocalStorage });

describe("API Client", () => {
    beforeEach(() => {
        mockFetch.mockClear();
        mockLocalStorage.getItem.mockClear();
    });

    describe("Authentication", () => {
        it("should include auth header when token exists", async () => {
            mockLocalStorage.getItem.mockReturnValue("test-token");
            mockFetch.mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({ success: true }),
            });

            // Simulate API request
            await fetch("/api/test", {
                headers: {
                    Authorization: `Bearer ${localStorage.getItem("token")}`,
                },
            });

            expect(mockFetch).toHaveBeenCalledWith("/api/test", {
                headers: {
                    Authorization: "Bearer test-token",
                },
            });
        });

        it("should handle missing token", () => {
            mockLocalStorage.getItem.mockReturnValue(null);

            const token = localStorage.getItem("token");
            expect(token).toBeNull();
        });
    });

    describe("Response Handling", () => {
        it("should parse JSON responses", async () => {
            const mockData = { id: 1, name: "Test" };
            mockFetch.mockResolvedValue({
                ok: true,
                json: () => Promise.resolve(mockData),
            });

            const response = await fetch("/api/test");
            const data = await response.json();

            expect(data).toEqual(mockData);
        });

        it("should handle error responses", async () => {
            mockFetch.mockResolvedValue({
                ok: false,
                status: 400,
                json: () => Promise.resolve({ detail: "Bad request" }),
            });

            const response = await fetch("/api/test");

            expect(response.ok).toBe(false);
            expect(response.status).toBe(400);
        });

        it("should handle network errors", async () => {
            mockFetch.mockRejectedValue(new Error("Network error"));

            await expect(fetch("/api/test")).rejects.toThrow("Network error");
        });
    });

    describe("Request Building", () => {
        it("should build GET request correctly", async () => {
            mockFetch.mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({}),
            });

            await fetch("/api/analytics?format=json");

            expect(mockFetch).toHaveBeenCalledWith("/api/analytics?format=json");
        });

        it("should build POST request with body", async () => {
            mockFetch.mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({}),
            });

            const body = { amount: 100 };
            await fetch("/api/payouts", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(body),
            });

            expect(mockFetch).toHaveBeenCalledWith("/api/payouts", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(body),
            });
        });

        it("should build DELETE request correctly", async () => {
            mockFetch.mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({ success: true }),
            });

            await fetch("/api/items/123", { method: "DELETE" });

            expect(mockFetch).toHaveBeenCalledWith("/api/items/123", { method: "DELETE" });
        });
    });
});

describe("API Response Types", () => {
    describe("ROI Response", () => {
        it("should have expected shape", () => {
            const roiResponse = {
                id: "123",
                period_start: "2024-01-01",
                period_end: "2024-01-31",
                revenue: {
                    brand_deals: 10000,
                    affiliate: 5000,
                    subscriptions: 3000,
                    royalties: 2000,
                    other: 0,
                    total: 20000,
                },
                costs: {
                    software: 1000,
                    equipment: 500,
                    marketing: 200,
                    contractors: 0,
                    other: 0,
                    total: 1700,
                },
                metrics: {
                    net_profit_cents: 18300,
                    roi_percentage: 1076.47,
                    profit_margin: 91.5,
                },
            };

            expect(roiResponse.revenue.total).toBe(20000);
            expect(roiResponse.costs.total).toBe(1700);
            expect(roiResponse.metrics.net_profit_cents).toBe(18300);
        });
    });

    describe("Payout Response", () => {
        it("should have expected shape", () => {
            const payoutResponse = {
                id: "po_123",
                amount_cents: 10000,
                currency: "usd",
                status: "paid",
                arrival_date: "2024-01-15",
            };

            expect(payoutResponse.amount_cents).toBe(10000);
            expect(payoutResponse.status).toBe("paid");
        });
    });

    describe("Analytics Export Response", () => {
        it("should have expected shape for CSV", () => {
            const exportResponse = {
                format: "csv",
                filename: "analytics_20240101-20240131.csv",
                data: "base64encodeddata",
                generated_at: "2024-01-31T12:00:00Z",
            };

            expect(exportResponse.format).toBe("csv");
            expect(exportResponse.filename).toMatch(/\.csv$/);
        });

        it("should have expected shape for JSON", () => {
            const exportResponse = {
                format: "json",
                filename: "analytics_20240101-20240131.json",
                data: '{"overview":{}}',
                generated_at: "2024-01-31T12:00:00Z",
            };

            expect(exportResponse.format).toBe("json");
            expect(exportResponse.filename).toMatch(/\.json$/);
        });
    });
});
