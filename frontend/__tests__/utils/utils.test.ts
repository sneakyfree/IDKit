import { cn, formatCount, formatRelativeTime } from "@/lib/utils";

describe("cn (classnames utility)", () => {
  it("should merge class names", () => {
    expect(cn("foo", "bar")).toBe("foo bar");
  });

  it("should handle conditional classes", () => {
    expect(cn("foo", false && "bar", "baz")).toBe("foo baz");
    expect(cn("foo", true && "bar", "baz")).toBe("foo bar baz");
  });

  it("should merge Tailwind classes correctly", () => {
    expect(cn("px-2", "px-4")).toBe("px-4");
    expect(cn("text-red-500", "text-blue-500")).toBe("text-blue-500");
  });

  it("should handle arrays", () => {
    expect(cn(["foo", "bar"])).toBe("foo bar");
  });

  it("should handle objects", () => {
    expect(cn({ foo: true, bar: false, baz: true })).toBe("foo baz");
  });

  it("should handle empty inputs", () => {
    expect(cn()).toBe("");
    expect(cn("")).toBe("");
    expect(cn(null, undefined)).toBe("");
  });
});

describe("formatCount", () => {
  it("should format numbers under 1000", () => {
    expect(formatCount(0)).toBe("0");
    expect(formatCount(1)).toBe("1");
    expect(formatCount(999)).toBe("999");
  });

  it("should format thousands with K suffix", () => {
    expect(formatCount(1000)).toBe("1K");
    expect(formatCount(1500)).toBe("1.5K");
    expect(formatCount(10000)).toBe("10K");
    expect(formatCount(999999)).toBe("1000K");
  });

  it("should format millions with M suffix", () => {
    expect(formatCount(1000000)).toBe("1M");
    expect(formatCount(1500000)).toBe("1.5M");
    expect(formatCount(10000000)).toBe("10M");
  });

  it("should remove trailing .0", () => {
    expect(formatCount(2000)).toBe("2K");
    expect(formatCount(3000000)).toBe("3M");
  });
});

describe("formatRelativeTime", () => {
  const now = new Date();

  it("should return 'just now' for recent times", () => {
    const date = new Date(now.getTime() - 30 * 1000); // 30 seconds ago
    expect(formatRelativeTime(date.toISOString())).toBe("just now");
  });

  it("should format minutes ago", () => {
    const date = new Date(now.getTime() - 5 * 60 * 1000); // 5 minutes ago
    expect(formatRelativeTime(date.toISOString())).toBe("5m");
  });

  it("should format hours ago", () => {
    const date = new Date(now.getTime() - 3 * 60 * 60 * 1000); // 3 hours ago
    expect(formatRelativeTime(date.toISOString())).toBe("3h");
  });

  it("should format days ago", () => {
    const date = new Date(now.getTime() - 2 * 24 * 60 * 60 * 1000); // 2 days ago
    expect(formatRelativeTime(date.toISOString())).toBe("2d");
  });

  it("should format weeks ago", () => {
    const date = new Date(now.getTime() - 2 * 7 * 24 * 60 * 60 * 1000); // 2 weeks ago
    expect(formatRelativeTime(date.toISOString())).toBe("2w");
  });

  it("should format older dates with month and day", () => {
    const date = new Date(now.getTime() - 60 * 24 * 60 * 60 * 1000); // 60 days ago
    const result = formatRelativeTime(date.toISOString());
    expect(result).toMatch(/[A-Z][a-z]{2} \d{1,2}/); // e.g., "Nov 10"
  });
});
