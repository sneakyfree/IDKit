"use client";

import { useRef, useEffect, useCallback } from "react";

interface FocusTrapProps {
  children: React.ReactNode;
  active?: boolean;
  restoreFocus?: boolean;
  autoFocus?: boolean;
}

const FOCUSABLE_ELEMENTS = [
  "a[href]",
  "button:not([disabled])",
  "input:not([disabled])",
  "select:not([disabled])",
  "textarea:not([disabled])",
  '[tabindex]:not([tabindex="-1"])',
].join(", ");

export function FocusTrap({
  children,
  active = true,
  restoreFocus = true,
  autoFocus = true,
}: FocusTrapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const previousActiveElement = useRef<HTMLElement | null>(null);

  const getFocusableElements = useCallback(() => {
    if (!containerRef.current) return [];
    return Array.from(
      containerRef.current.querySelectorAll<HTMLElement>(FOCUSABLE_ELEMENTS)
    ).filter((el) => el.offsetParent !== null); // Filter out hidden elements
  }, []);

  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (!active || event.key !== "Tab") return;

      const focusableElements = getFocusableElements();
      if (focusableElements.length === 0) return;

      const firstElement = focusableElements[0];
      const lastElement = focusableElements[focusableElements.length - 1];

      if (event.shiftKey) {
        // Shift + Tab: move backward
        if (document.activeElement === firstElement) {
          event.preventDefault();
          lastElement.focus();
        }
      } else {
        // Tab: move forward
        if (document.activeElement === lastElement) {
          event.preventDefault();
          firstElement.focus();
        }
      }
    },
    [active, getFocusableElements]
  );

  useEffect(() => {
    if (!active) return;

    // Store the previously focused element
    if (restoreFocus) {
      previousActiveElement.current = document.activeElement as HTMLElement;
    }

    // Auto focus the first focusable element
    if (autoFocus) {
      const focusableElements = getFocusableElements();
      if (focusableElements.length > 0) {
        focusableElements[0].focus();
      }
    }

    // Add keyboard listener
    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.removeEventListener("keydown", handleKeyDown);

      // Restore focus on cleanup
      if (restoreFocus && previousActiveElement.current) {
        previousActiveElement.current.focus();
      }
    };
  }, [active, autoFocus, restoreFocus, getFocusableElements, handleKeyDown]);

  return (
    <div ref={containerRef} data-focus-trap={active}>
      {children}
    </div>
  );
}

// Hook for manual focus management
export function useFocusManagement() {
  const focusFirst = useCallback((container: HTMLElement | null) => {
    if (!container) return;
    const focusable = container.querySelector<HTMLElement>(FOCUSABLE_ELEMENTS);
    focusable?.focus();
  }, []);

  const focusLast = useCallback((container: HTMLElement | null) => {
    if (!container) return;
    const focusables = container.querySelectorAll<HTMLElement>(FOCUSABLE_ELEMENTS);
    if (focusables.length > 0) {
      focusables[focusables.length - 1].focus();
    }
  }, []);

  const focusElement = useCallback((selector: string, container?: HTMLElement) => {
    const root = container || document;
    const element = root.querySelector<HTMLElement>(selector);
    element?.focus();
  }, []);

  return {
    focusFirst,
    focusLast,
    focusElement,
    FOCUSABLE_ELEMENTS,
  };
}

export default FocusTrap;
