import { render, screen, fireEvent } from "@testing-library/react";

// Mock the store
const mockSetTheme = jest.fn();
jest.mock("@/lib/store", () => ({
  useThemeStore: jest.fn((selector) =>
    selector({
      theme: "dark",
      resolvedTheme: "dark",
      setTheme: mockSetTheme,
      initializeTheme: jest.fn(),
    })
  ),
}));

describe("ThemeToggle", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("dropdown variant", () => {
    it("should render dropdown trigger", async () => {
      const { ThemeToggle } = await import("@/components/settings/ThemeToggle");
      render(<ThemeToggle variant="dropdown" />);

      expect(screen.getByRole("button")).toBeInTheDocument();
    });

    it("should show dropdown menu on click", async () => {
      const { ThemeToggle } = await import("@/components/settings/ThemeToggle");
      render(<ThemeToggle variant="dropdown" />);

      const trigger = screen.getByRole("button");
      fireEvent.click(trigger);

      expect(screen.getByText("Light")).toBeInTheDocument();
      expect(screen.getByText("Dark")).toBeInTheDocument();
      expect(screen.getByText("System")).toBeInTheDocument();
    });

    it("should call setTheme when selecting a theme", async () => {
      const { ThemeToggle } = await import("@/components/settings/ThemeToggle");
      render(<ThemeToggle variant="dropdown" />);

      const trigger = screen.getByRole("button");
      fireEvent.click(trigger);

      const lightOption = screen.getByText("Light");
      fireEvent.click(lightOption);

      expect(mockSetTheme).toHaveBeenCalledWith("light");
    });
  });

  describe("buttons variant", () => {
    it("should render all theme buttons", async () => {
      const { ThemeToggle } = await import("@/components/settings/ThemeToggle");
      render(<ThemeToggle variant="buttons" />);

      const buttons = screen.getAllByRole("button");
      expect(buttons).toHaveLength(3); // Light, Dark, System
    });

    it("should highlight current theme button", async () => {
      const { ThemeToggle } = await import("@/components/settings/ThemeToggle");
      render(<ThemeToggle variant="buttons" />);

      const buttons = screen.getAllByRole("button");
      // Dark should be active (has bg-gray-700 class)
      const darkButton = buttons[1];
      expect(darkButton).toHaveClass("bg-gray-700");
    });

    it("should call setTheme when clicking a theme button", async () => {
      const { ThemeToggle } = await import("@/components/settings/ThemeToggle");
      render(<ThemeToggle variant="buttons" />);

      const buttons = screen.getAllByRole("button");
      const lightButton = buttons[0];
      fireEvent.click(lightButton);

      expect(mockSetTheme).toHaveBeenCalledWith("light");
    });
  });

  describe("switch variant", () => {
    it("should render toggle switch", async () => {
      const { ThemeToggle } = await import("@/components/settings/ThemeToggle");
      render(<ThemeToggle variant="switch" />);

      expect(screen.getByRole("button")).toBeInTheDocument();
    });

    it("should toggle between light and dark", async () => {
      const { ThemeToggle } = await import("@/components/settings/ThemeToggle");
      render(<ThemeToggle variant="switch" />);

      const toggle = screen.getByRole("button");
      fireEvent.click(toggle);

      // When dark, clicking should switch to light
      expect(mockSetTheme).toHaveBeenCalledWith("light");
    });
  });
});
