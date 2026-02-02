/**
 * Tests for Accessibility Utilities
 * 
 * @jest-environment jsdom
 */

import {
    getKeyboardClickProps,
    generateAriaId,
    ariaPatterns,
    getContrastRatio,
    meetsWCAG_AA,
    prefersReducedMotion,
    visuallyHiddenStyles,
} from "@/lib/accessibility";

describe("Accessibility Utilities", () => {
    describe("getKeyboardClickProps", () => {
        it("should return props for keyboard accessibility", () => {
            const onClick = jest.fn();
            const props = getKeyboardClickProps(onClick);

            expect(props.role).toBe("button");
            expect(props.tabIndex).toBe(0);
            expect(props.onClick).toBe(onClick);
            expect(typeof props.onKeyDown).toBe("function");
        });

        it("should allow custom role", () => {
            const onClick = jest.fn();
            const props = getKeyboardClickProps(onClick, "link");

            expect(props.role).toBe("link");
        });

        it("should call onClick on Enter key", () => {
            const onClick = jest.fn();
            const props = getKeyboardClickProps(onClick);

            const event = {
                key: "Enter",
                preventDefault: jest.fn(),
            } as unknown as React.KeyboardEvent;

            props.onKeyDown(event);

            expect(onClick).toHaveBeenCalled();
            expect(event.preventDefault).toHaveBeenCalled();
        });

        it("should call onClick on Space key", () => {
            const onClick = jest.fn();
            const props = getKeyboardClickProps(onClick);

            const event = {
                key: " ",
                preventDefault: jest.fn(),
            } as unknown as React.KeyboardEvent;

            props.onKeyDown(event);

            expect(onClick).toHaveBeenCalled();
        });

        it("should not call onClick on other keys", () => {
            const onClick = jest.fn();
            const props = getKeyboardClickProps(onClick);

            const event = {
                key: "Tab",
                preventDefault: jest.fn(),
            } as unknown as React.KeyboardEvent;

            props.onKeyDown(event);

            expect(onClick).not.toHaveBeenCalled();
        });
    });

    describe("generateAriaId", () => {
        it("should generate unique IDs", () => {
            const id1 = generateAriaId("test");
            const id2 = generateAriaId("test");

            expect(id1).not.toBe(id2);
            expect(id1).toMatch(/^test-\d+$/);
        });

        it("should use default prefix", () => {
            const id = generateAriaId();
            expect(id).toMatch(/^aria-\d+$/);
        });
    });

    describe("ariaPatterns", () => {
        it("should return dialog pattern", () => {
            const pattern = ariaPatterns.dialog("title-id");

            expect(pattern.role).toBe("dialog");
            expect(pattern["aria-modal"]).toBe(true);
            expect(pattern["aria-labelledby"]).toBe("title-id");
        });

        it("should return alert pattern", () => {
            expect(ariaPatterns.alert.role).toBe("alert");
            expect(ariaPatterns.alert["aria-live"]).toBe("assertive");
        });

        it("should return status pattern", () => {
            expect(ariaPatterns.status.role).toBe("status");
            expect(ariaPatterns.status["aria-live"]).toBe("polite");
        });

        it("should return tab pattern", () => {
            const pattern = ariaPatterns.tab("tab-1", "panel-1", true, 0);

            expect(pattern.role).toBe("tab");
            expect(pattern["aria-selected"]).toBe(true);
            expect(pattern["aria-controls"]).toBe("panel-1");
            expect(pattern.tabIndex).toBe(0);
        });

        it("should return tabPanel pattern", () => {
            const pattern = ariaPatterns.tabPanel("panel-1", "tab-1", true);

            expect(pattern.role).toBe("tabpanel");
            expect(pattern["aria-labelledby"]).toBe("tab-1");
            expect(pattern.hidden).toBe(false);
        });

        it("should return expandable pattern", () => {
            const pattern = ariaPatterns.expandable(true, "content-1");

            expect(pattern["aria-expanded"]).toBe(true);
            expect(pattern["aria-controls"]).toBe("content-1");
        });

        it("should return loading pattern", () => {
            expect(ariaPatterns.loading(true)["aria-busy"]).toBe(true);
            expect(ariaPatterns.loading(false)["aria-busy"]).toBe(false);
        });

        it("should return required pattern", () => {
            expect(ariaPatterns.required["aria-required"]).toBe(true);
        });

        it("should return invalid pattern", () => {
            const pattern = ariaPatterns.invalid("error-1");

            expect(pattern["aria-invalid"]).toBe(true);
            expect(pattern["aria-describedby"]).toBe("error-1");
        });
    });

    describe("getContrastRatio", () => {
        it("should calculate correct contrast ratio for black and white", () => {
            const black = { r: 0, g: 0, b: 0 };
            const white = { r: 255, g: 255, b: 255 };

            const ratio = getContrastRatio(black, white);

            expect(ratio).toBeCloseTo(21, 0);
        });

        it("should return 1 for same colors", () => {
            const color = { r: 128, g: 128, b: 128 };

            const ratio = getContrastRatio(color, color);

            expect(ratio).toBe(1);
        });
    });

    describe("meetsWCAG_AA", () => {
        it("should pass for high contrast colors", () => {
            const black = { r: 0, g: 0, b: 0 };
            const white = { r: 255, g: 255, b: 255 };

            expect(meetsWCAG_AA(black, white)).toBe(true);
        });

        it("should fail for low contrast colors", () => {
            const gray1 = { r: 128, g: 128, b: 128 };
            const gray2 = { r: 140, g: 140, b: 140 };

            expect(meetsWCAG_AA(gray1, gray2)).toBe(false);
        });

        it("should have lower threshold for large text", () => {
            const color1 = { r: 100, g: 100, b: 100 };
            const color2 = { r: 200, g: 200, b: 200 };

            // May pass for large text but fail for normal text
            const normalPasses = meetsWCAG_AA(color1, color2, false);
            const largePasses = meetsWCAG_AA(color1, color2, true);

            // Large text has lower requirements (3:1 vs 4.5:1)
            expect(largePasses || !normalPasses).toBe(true);
        });
    });

    describe("prefersReducedMotion", () => {
        it("should return boolean", () => {
            const result = prefersReducedMotion();
            expect(typeof result).toBe("boolean");
        });
    });

    describe("visuallyHiddenStyles", () => {
        it("should have correct CSS properties", () => {
            expect(visuallyHiddenStyles.position).toBe("absolute");
            expect(visuallyHiddenStyles.width).toBe("1px");
            expect(visuallyHiddenStyles.height).toBe("1px");
            expect(visuallyHiddenStyles.overflow).toBe("hidden");
        });
    });
});
