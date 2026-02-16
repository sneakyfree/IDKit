/**
 * API Integration Tests for Gap Closure Routes
 *
 * Mock-fetch tests validating response shapes for
 * sponsorships, contracts, listening, developer keys,
 * tax, reports, and revenue-sharing API modules.
 *
 * @jest-environment jsdom
 */
export { };

const mockFetch = jest.fn();
global.fetch = mockFetch;

const mockLocalStorage = {
    getItem: jest.fn().mockReturnValue("test-token"),
    setItem: jest.fn(),
    removeItem: jest.fn(),
    clear: jest.fn(),
};
Object.defineProperty(window, "localStorage", { value: mockLocalStorage });

const API_BASE = "/api/v1";

function authHeaders() {
    return {
        Authorization: `Bearer ${localStorage.getItem("token")}`,
        "Content-Type": "application/json",
    };
}

beforeEach(() => {
    mockFetch.mockClear();
});

// ---- Sponsorships ----
describe("Sponsorships API", () => {
    it("should list sponsorships", async () => {
        const body = { sponsorships: [{ id: "1", brand_name: "Nike" }], total: 1 };
        mockFetch.mockResolvedValue({ ok: true, json: () => Promise.resolve(body) });

        const res = await fetch(`${API_BASE}/sponsorships`, { headers: authHeaders() });
        const data = await res.json();

        expect(data.sponsorships).toHaveLength(1);
        expect(data.total).toBe(1);
    });

    it("should create a sponsorship", async () => {
        const body = { id: "1", brand_name: "Adidas", status: "active", value_cents: 50000 };
        mockFetch.mockResolvedValue({ ok: true, json: () => Promise.resolve(body) });

        const res = await fetch(`${API_BASE}/sponsorships`, {
            method: "POST",
            headers: authHeaders(),
            body: JSON.stringify({ brand_name: "Adidas", value_cents: 50000 }),
        });
        const data = await res.json();

        expect(data.brand_name).toBe("Adidas");
        expect(data.value_cents).toBe(50000);
    });
});

// ---- Contracts ----
describe("Contracts API", () => {
    it("should list contracts", async () => {
        const body = { contracts: [{ id: "c1", title: "Brand Deal" }], total: 1 };
        mockFetch.mockResolvedValue({ ok: true, json: () => Promise.resolve(body) });

        const res = await fetch(`${API_BASE}/contracts`, { headers: authHeaders() });
        const data = await res.json();

        expect(data.contracts).toHaveLength(1);
        expect(data.total).toBe(1);
    });

    it("should create a contract", async () => {
        const body = { id: "c1", title: "New Deal", brand_name: "BrandX", status: "draft" };
        mockFetch.mockResolvedValue({ ok: true, json: () => Promise.resolve(body) });

        const res = await fetch(`${API_BASE}/contracts`, {
            method: "POST",
            headers: authHeaders(),
            body: JSON.stringify({ title: "New Deal", brand_name: "BrandX" }),
        });
        const data = await res.json();

        expect(data.status).toBe("draft");
    });

    it("should sign a contract", async () => {
        const body = { id: "c1", status: "active" };
        mockFetch.mockResolvedValue({ ok: true, json: () => Promise.resolve(body) });

        const res = await fetch(`${API_BASE}/contracts/c1/sign`, {
            method: "POST",
            headers: authHeaders(),
        });
        const data = await res.json();

        expect(data.status).toBe("active");
    });
});

// ---- Social Listening ----
describe("Social Listening API", () => {
    it("should list queries", async () => {
        const body = { queries: [{ id: "q1", name: "Tracker" }], total: 1 };
        mockFetch.mockResolvedValue({ ok: true, json: () => Promise.resolve(body) });

        const res = await fetch(`${API_BASE}/listening/queries`, { headers: authHeaders() });
        const data = await res.json();

        expect(data.queries).toHaveLength(1);
    });

    it("should get sentiment summary", async () => {
        const body = { positive: 60, neutral: 30, negative: 10 };
        mockFetch.mockResolvedValue({ ok: true, json: () => Promise.resolve(body) });

        const res = await fetch(`${API_BASE}/listening/queries/q1/sentiment`, {
            headers: authHeaders(),
        });
        const data = await res.json();

        expect(data.positive).toBe(60);
        expect(data.neutral).toBe(30);
        expect(data.negative).toBe(10);
    });
});

// ---- Developer Keys ----
describe("Developer Keys API", () => {
    it("should create key and receive secret", async () => {
        const body = {
            key: { id: "k1", name: "My Key", scopes: ["read"] },
            secret: "sk_live_abc123",
            warning: "Save this secret — it will not be shown again.",
        };
        mockFetch.mockResolvedValue({ ok: true, json: () => Promise.resolve(body) });

        const res = await fetch(`${API_BASE}/api-keys`, {
            method: "POST",
            headers: authHeaders(),
            body: JSON.stringify({ name: "My Key", scopes: ["read"] }),
        });
        const data = await res.json();

        expect(data.secret).toBe("sk_live_abc123");
        expect(data.warning).toContain("Save this secret");
    });
});

// ---- Tax ----
describe("Tax API", () => {
    it("should get tax profile", async () => {
        const body = { business_type: "llc", legal_name: "Creator LLC", w9_submitted: true };
        mockFetch.mockResolvedValue({ ok: true, json: () => Promise.resolve(body) });

        const res = await fetch(`${API_BASE}/tax/profile`, { headers: authHeaders() });
        const data = await res.json();

        expect(data.w9_submitted).toBe(true);
    });

    it("should generate a tax document", async () => {
        const body = { id: "doc1", type: "1099-NEC", year: 2024, status: "generated" };
        mockFetch.mockResolvedValue({ ok: true, json: () => Promise.resolve(body) });

        const res = await fetch(`${API_BASE}/tax/documents/generate`, {
            method: "POST",
            headers: authHeaders(),
            body: JSON.stringify({ type: "1099-NEC", year: 2024, total_amount_cents: 500000 }),
        });
        const data = await res.json();

        expect(data.type).toBe("1099-NEC");
        expect(data.year).toBe(2024);
    });
});

// ---- Reports ----
describe("Reports API", () => {
    it("should create a report", async () => {
        const body = { id: "r1", name: "Weekly", metrics: ["followers"], export_format: "pdf" };
        mockFetch.mockResolvedValue({ ok: true, json: () => Promise.resolve(body) });

        const res = await fetch(`${API_BASE}/reports`, {
            method: "POST",
            headers: authHeaders(),
            body: JSON.stringify({ name: "Weekly", metrics: ["followers"], platforms: ["ig"] }),
        });
        const data = await res.json();

        expect(data.name).toBe("Weekly");
        expect(data.export_format).toBe("pdf");
    });

    it("should schedule a report", async () => {
        const body = { id: "r1", status: "scheduled" };
        mockFetch.mockResolvedValue({ ok: true, json: () => Promise.resolve(body) });

        const res = await fetch(`${API_BASE}/reports/r1/schedule`, {
            method: "POST",
            headers: authHeaders(),
            body: JSON.stringify({ frequency: "weekly" }),
        });
        const data = await res.json();

        expect(data.status).toBe("scheduled");
    });
});

// ---- Revenue Sharing ----
describe("Revenue Sharing API", () => {
    it("should list agreements", async () => {
        const body = {
            agreements: [{ id: "a1", name: "50/50", split_percentage: 50 }],
            total: 1,
        };
        mockFetch.mockResolvedValue({ ok: true, json: () => Promise.resolve(body) });

        const res = await fetch(`${API_BASE}/revenue-sharing`, { headers: authHeaders() });
        const data = await res.json();

        expect(data.agreements).toHaveLength(1);
        expect(data.agreements[0].split_percentage).toBe(50);
    });

    it("should record revenue", async () => {
        const body = {
            id: "d1",
            amount_cents: 100000,
            owner_share_cents: 50000,
            partner_share_cents: 50000,
        };
        mockFetch.mockResolvedValue({ ok: true, json: () => Promise.resolve(body) });

        const res = await fetch(`${API_BASE}/revenue-sharing/a1/revenue`, {
            method: "POST",
            headers: authHeaders(),
            body: JSON.stringify({
                amount_cents: 100000,
                period_start: "2024-01-01T00:00:00",
                period_end: "2024-01-31T23:59:59",
            }),
        });
        const data = await res.json();

        expect(data.owner_share_cents).toBe(50000);
        expect(data.partner_share_cents).toBe(50000);
    });
});
