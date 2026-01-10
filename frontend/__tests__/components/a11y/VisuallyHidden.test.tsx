import { render, screen } from "@testing-library/react";

describe("VisuallyHidden", () => {
  it("should render children with visually hidden styles", async () => {
    const { VisuallyHidden } = await import("@/components/a11y/VisuallyHidden");
    render(<VisuallyHidden>Hidden text</VisuallyHidden>);

    const element = screen.getByText("Hidden text");
    expect(element).toBeInTheDocument();

    // Check visually hidden styles
    const styles = window.getComputedStyle(element);
    expect(element).toHaveClass("sr-only");
  });

  it("should render as span by default", async () => {
    const { VisuallyHidden } = await import("@/components/a11y/VisuallyHidden");
    render(<VisuallyHidden>Hidden text</VisuallyHidden>);

    const element = screen.getByText("Hidden text");
    expect(element.tagName).toBe("SPAN");
  });

  it("should render as specified element", async () => {
    const { VisuallyHidden } = await import("@/components/a11y/VisuallyHidden");
    render(<VisuallyHidden as="div">Hidden text</VisuallyHidden>);

    const element = screen.getByText("Hidden text");
    expect(element.tagName).toBe("DIV");
  });

  it("should be accessible to screen readers", async () => {
    const { VisuallyHidden } = await import("@/components/a11y/VisuallyHidden");
    render(
      <button>
        Click me
        <VisuallyHidden>for more information</VisuallyHidden>
      </button>
    );

    const button = screen.getByRole("button", {
      name: /click me for more information/i,
    });
    expect(button).toBeInTheDocument();
  });
});
