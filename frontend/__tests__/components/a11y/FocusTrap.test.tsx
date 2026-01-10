import { render, screen, fireEvent } from "@testing-library/react";

describe("FocusTrap", () => {
  beforeEach(() => {
    // Reset focus to body
    document.body.focus();
  });

  it("should render children", async () => {
    const { FocusTrap } = await import("@/components/a11y/FocusTrap");
    render(
      <FocusTrap>
        <button>Button 1</button>
        <button>Button 2</button>
      </FocusTrap>
    );

    expect(screen.getByText("Button 1")).toBeInTheDocument();
    expect(screen.getByText("Button 2")).toBeInTheDocument();
  });

  it("should auto-focus first focusable element when active", async () => {
    const { FocusTrap } = await import("@/components/a11y/FocusTrap");
    render(
      <FocusTrap active={true} autoFocus={true}>
        <button>Button 1</button>
        <button>Button 2</button>
      </FocusTrap>
    );

    expect(document.activeElement).toBe(screen.getByText("Button 1"));
  });

  it("should not auto-focus when autoFocus is false", async () => {
    const { FocusTrap } = await import("@/components/a11y/FocusTrap");
    const previousActive = document.activeElement;

    render(
      <FocusTrap active={true} autoFocus={false}>
        <button>Button 1</button>
        <button>Button 2</button>
      </FocusTrap>
    );

    expect(document.activeElement).toBe(previousActive);
  });

  it("should not trap focus when inactive", async () => {
    const { FocusTrap } = await import("@/components/a11y/FocusTrap");
    render(
      <FocusTrap active={false}>
        <button>Button 1</button>
        <button>Button 2</button>
      </FocusTrap>
    );

    // First button should not be auto-focused
    expect(document.activeElement).not.toBe(screen.getByText("Button 1"));
  });

  it("should wrap focus from last to first element on Tab", async () => {
    const { FocusTrap } = await import("@/components/a11y/FocusTrap");
    render(
      <FocusTrap active={true} autoFocus={false}>
        <button>Button 1</button>
        <button>Button 2</button>
        <button>Button 3</button>
      </FocusTrap>
    );

    // Focus the last button
    const button3 = screen.getByText("Button 3");
    button3.focus();
    expect(document.activeElement).toBe(button3);

    // Simulate Tab key
    fireEvent.keyDown(document, { key: "Tab", shiftKey: false });

    // Should wrap to first button
    expect(document.activeElement).toBe(screen.getByText("Button 1"));
  });

  it("should wrap focus from first to last element on Shift+Tab", async () => {
    const { FocusTrap } = await import("@/components/a11y/FocusTrap");
    render(
      <FocusTrap active={true} autoFocus={true}>
        <button>Button 1</button>
        <button>Button 2</button>
        <button>Button 3</button>
      </FocusTrap>
    );

    // First button is auto-focused
    expect(document.activeElement).toBe(screen.getByText("Button 1"));

    // Simulate Shift+Tab
    fireEvent.keyDown(document, { key: "Tab", shiftKey: true });

    // Should wrap to last button
    expect(document.activeElement).toBe(screen.getByText("Button 3"));
  });

  it("should add data-focus-trap attribute", async () => {
    const { FocusTrap } = await import("@/components/a11y/FocusTrap");
    const { container } = render(
      <FocusTrap active={true}>
        <button>Button</button>
      </FocusTrap>
    );

    const trapElement = container.querySelector("[data-focus-trap]");
    expect(trapElement).toBeInTheDocument();
    expect(trapElement).toHaveAttribute("data-focus-trap", "true");
  });

  it("should not focus disabled elements", async () => {
    const { FocusTrap } = await import("@/components/a11y/FocusTrap");
    render(
      <FocusTrap active={true} autoFocus={true}>
        <button disabled>Disabled Button</button>
        <button>Enabled Button</button>
      </FocusTrap>
    );

    // Should focus the enabled button, not the disabled one
    expect(document.activeElement).toBe(screen.getByText("Enabled Button"));
  });
});

describe("useFocusManagement", () => {
  it("should focus first element in container", async () => {
    const { useFocusManagement } = await import("@/components/a11y/FocusTrap");
    const TestComponent = () => {
      const { focusFirst } = useFocusManagement();

      return (
        <div
          ref={(el) => {
            if (el) focusFirst(el);
          }}
        >
          <button>First</button>
          <button>Second</button>
        </div>
      );
    };

    render(<TestComponent />);
    expect(document.activeElement).toBe(screen.getByText("First"));
  });

  it("should focus last element in container", async () => {
    const { useFocusManagement } = await import("@/components/a11y/FocusTrap");
    const TestComponent = () => {
      const { focusLast } = useFocusManagement();

      return (
        <div
          ref={(el) => {
            if (el) focusLast(el);
          }}
        >
          <button>First</button>
          <button>Last</button>
        </div>
      );
    };

    render(<TestComponent />);
    expect(document.activeElement).toBe(screen.getByText("Last"));
  });
});
