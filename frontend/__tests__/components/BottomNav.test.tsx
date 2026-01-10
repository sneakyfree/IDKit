import { render, screen, fireEvent } from "@testing-library/react";

// Mock next/navigation
jest.mock("next/navigation", () => ({
  usePathname: jest.fn(() => "/"),
}));

// Mock the store
const mockOpenCreate = jest.fn();
jest.mock("@/lib/store", () => ({
  useCreateStore: jest.fn((selector) =>
    selector({ isOpen: false, open: mockOpenCreate, close: jest.fn() })
  ),
}));

describe("BottomNav", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("should render navigation items", async () => {
    const { BottomNav } = await import("@/components/nav/BottomNav");
    render(<BottomNav />);

    expect(screen.getByText("Home")).toBeInTheDocument();
    expect(screen.getByText("Discover")).toBeInTheDocument();
    expect(screen.getByText("Inbox")).toBeInTheDocument();
    expect(screen.getByText("Profile")).toBeInTheDocument();
  });

  it("should have correct links", async () => {
    const { BottomNav } = await import("@/components/nav/BottomNav");
    render(<BottomNav />);

    const homeLink = screen.getByText("Home").closest("a");
    const discoverLink = screen.getByText("Discover").closest("a");
    const inboxLink = screen.getByText("Inbox").closest("a");
    const profileLink = screen.getByText("Profile").closest("a");

    expect(homeLink).toHaveAttribute("href", "/");
    expect(discoverLink).toHaveAttribute("href", "/discover");
    expect(inboxLink).toHaveAttribute("href", "/inbox");
    expect(profileLink).toHaveAttribute("href", "/profile");
  });

  it("should highlight active route", async () => {
    const { usePathname } = await import("next/navigation");
    (usePathname as jest.Mock).mockReturnValue("/discover");

    const { BottomNav } = await import("@/components/nav/BottomNav");
    render(<BottomNav />);

    const discoverLink = screen.getByText("Discover").closest("a");
    expect(discoverLink).toHaveClass("text-white");
  });

  it("should call open on create button click", async () => {
    const { BottomNav } = await import("@/components/nav/BottomNav");
    render(<BottomNav />);

    // Find the create button (it's a button, not a link)
    const createButton = screen.getByRole("button");
    fireEvent.click(createButton);

    expect(mockOpenCreate).toHaveBeenCalledTimes(1);
  });

  it("should render with fixed positioning", async () => {
    const { BottomNav } = await import("@/components/nav/BottomNav");
    const { container } = render(<BottomNav />);

    const nav = container.querySelector("nav");
    expect(nav).toHaveClass("fixed");
    expect(nav).toHaveClass("bottom-0");
  });
});
