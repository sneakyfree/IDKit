/**
 * TASK 5.4.1: Mobile UX Hooks and Utilities
 * 
 * Custom hooks for mobile-specific interactions
 */

import { useState, useCallback, useRef, useEffect } from "react";

// ============================================================================
// Pull to Refresh Hook
// ============================================================================

interface UsePullToRefreshOptions {
    onRefresh: () => Promise<void>;
    threshold?: number;
    disabled?: boolean;
}

export function usePullToRefresh({ onRefresh, threshold = 80, disabled = false }: UsePullToRefreshOptions) {
    const [pulling, setPulling] = useState(false);
    const [refreshing, setRefreshing] = useState(false);
    const [pullDistance, setPullDistance] = useState(0);
    const startY = useRef(0);
    const containerRef = useRef<HTMLDivElement>(null);

    const handleTouchStart = useCallback((e: TouchEvent) => {
        if (disabled || refreshing) return;
        if (window.scrollY !== 0) return;
        startY.current = e.touches[0].clientY;
        setPulling(true);
    }, [disabled, refreshing]);

    const handleTouchMove = useCallback((e: TouchEvent) => {
        if (!pulling || disabled || refreshing) return;

        const currentY = e.touches[0].clientY;
        const diff = currentY - startY.current;

        if (diff > 0 && window.scrollY === 0) {
            // Add resistance
            const resistance = 0.5;
            setPullDistance(Math.min(diff * resistance, threshold * 1.5));
            e.preventDefault();
        }
    }, [pulling, disabled, refreshing, threshold]);

    const handleTouchEnd = useCallback(async () => {
        if (!pulling) return;

        if (pullDistance >= threshold && !refreshing) {
            setRefreshing(true);
            try {
                await onRefresh();
            } finally {
                setRefreshing(false);
            }
        }

        setPulling(false);
        setPullDistance(0);
    }, [pulling, pullDistance, threshold, refreshing, onRefresh]);

    useEffect(() => {
        const container = containerRef.current;
        if (!container) return;

        container.addEventListener("touchstart", handleTouchStart, { passive: true });
        container.addEventListener("touchmove", handleTouchMove, { passive: false });
        container.addEventListener("touchend", handleTouchEnd);

        return () => {
            container.removeEventListener("touchstart", handleTouchStart);
            container.removeEventListener("touchmove", handleTouchMove);
            container.removeEventListener("touchend", handleTouchEnd);
        };
    }, [handleTouchStart, handleTouchMove, handleTouchEnd]);

    return {
        containerRef,
        refreshing,
        pullDistance,
        pullProgress: Math.min(pullDistance / threshold, 1),
    };
}

// ============================================================================
// Swipe Gesture Hook
// ============================================================================

type SwipeDirection = "left" | "right" | "up" | "down";

interface UseSwipeOptions {
    onSwipeLeft?: () => void;
    onSwipeRight?: () => void;
    onSwipeUp?: () => void;
    onSwipeDown?: () => void;
    threshold?: number;
    disabled?: boolean;
}

export function useSwipe({
    onSwipeLeft,
    onSwipeRight,
    onSwipeUp,
    onSwipeDown,
    threshold = 50,
    disabled = false,
}: UseSwipeOptions) {
    const [swiping, setSwiping] = useState(false);
    const [swipeOffset, setSwipeOffset] = useState({ x: 0, y: 0 });
    const startPos = useRef({ x: 0, y: 0 });
    const elementRef = useRef<HTMLDivElement>(null);

    const handleTouchStart = useCallback((e: TouchEvent) => {
        if (disabled) return;
        startPos.current = {
            x: e.touches[0].clientX,
            y: e.touches[0].clientY,
        };
        setSwiping(true);
    }, [disabled]);

    const handleTouchMove = useCallback((e: TouchEvent) => {
        if (!swiping || disabled) return;

        const currentX = e.touches[0].clientX;
        const currentY = e.touches[0].clientY;

        setSwipeOffset({
            x: currentX - startPos.current.x,
            y: currentY - startPos.current.y,
        });
    }, [swiping, disabled]);

    const handleTouchEnd = useCallback(() => {
        if (!swiping) return;

        const { x, y } = swipeOffset;
        const absX = Math.abs(x);
        const absY = Math.abs(y);

        // Determine primary swipe direction
        if (absX > absY && absX > threshold) {
            if (x > 0 && onSwipeRight) onSwipeRight();
            else if (x < 0 && onSwipeLeft) onSwipeLeft();
        } else if (absY > absX && absY > threshold) {
            if (y > 0 && onSwipeDown) onSwipeDown();
            else if (y < 0 && onSwipeUp) onSwipeUp();
        }

        setSwiping(false);
        setSwipeOffset({ x: 0, y: 0 });
    }, [swiping, swipeOffset, threshold, onSwipeLeft, onSwipeRight, onSwipeUp, onSwipeDown]);

    useEffect(() => {
        const element = elementRef.current;
        if (!element) return;

        element.addEventListener("touchstart", handleTouchStart, { passive: true });
        element.addEventListener("touchmove", handleTouchMove, { passive: true });
        element.addEventListener("touchend", handleTouchEnd);

        return () => {
            element.removeEventListener("touchstart", handleTouchStart);
            element.removeEventListener("touchmove", handleTouchMove);
            element.removeEventListener("touchend", handleTouchEnd);
        };
    }, [handleTouchStart, handleTouchMove, handleTouchEnd]);

    return {
        elementRef,
        swiping,
        swipeOffset,
    };
}

// ============================================================================
// Bottom Sheet Hook
// ============================================================================

interface UseBottomSheetOptions {
    initialOpen?: boolean;
    onClose?: () => void;
    snapPoints?: number[];
}

export function useBottomSheet({ initialOpen = false, onClose, snapPoints = [0.5, 1] }: UseBottomSheetOptions = {}) {
    const [isOpen, setIsOpen] = useState(initialOpen);
    const [snapIndex, setSnapIndex] = useState(0);
    const [dragOffset, setDragOffset] = useState(0);
    const sheetRef = useRef<HTMLDivElement>(null);
    const startY = useRef(0);

    const open = useCallback((snapTo = 0) => {
        setIsOpen(true);
        setSnapIndex(snapTo);
    }, []);

    const close = useCallback(() => {
        setIsOpen(false);
        setDragOffset(0);
        onClose?.();
    }, [onClose]);

    const handleDragStart = useCallback((e: TouchEvent) => {
        startY.current = e.touches[0].clientY;
    }, []);

    const handleDrag = useCallback((e: TouchEvent) => {
        const currentY = e.touches[0].clientY;
        const diff = currentY - startY.current;
        setDragOffset(Math.max(0, diff));
    }, []);

    const handleDragEnd = useCallback(() => {
        if (dragOffset > 100) {
            // Snap down or close
            if (snapIndex > 0) {
                setSnapIndex(snapIndex - 1);
            } else {
                close();
            }
        } else if (dragOffset < -50) {
            // Snap up
            if (snapIndex < snapPoints.length - 1) {
                setSnapIndex(snapIndex + 1);
            }
        }
        setDragOffset(0);
    }, [dragOffset, snapIndex, snapPoints.length, close]);

    const currentHeight = `${snapPoints[snapIndex] * 100}vh`;

    return {
        sheetRef,
        isOpen,
        open,
        close,
        currentHeight,
        dragOffset,
        handlers: {
            onTouchStart: handleDragStart,
            onTouchMove: handleDrag,
            onTouchEnd: handleDragEnd,
        },
    };
}

// ============================================================================
// Haptic Feedback Utility
// ============================================================================

export function triggerHaptic(type: "light" | "medium" | "heavy" | "selection" = "light") {
    if (typeof navigator === "undefined") return;

    if ("vibrate" in navigator) {
        const patterns = {
            light: [10],
            medium: [20],
            heavy: [30],
            selection: [5, 5, 5],
        };
        navigator.vibrate(patterns[type]);
    }
}

// ============================================================================
// Mobile Detection
// ============================================================================

export function useIsMobile() {
    const [isMobile, setIsMobile] = useState(false);

    useEffect(() => {
        const checkMobile = () => {
            setIsMobile(window.innerWidth < 768);
        };

        checkMobile();
        window.addEventListener("resize", checkMobile);
        return () => window.removeEventListener("resize", checkMobile);
    }, []);

    return isMobile;
}

export function useIsTouch() {
    const [isTouch, setIsTouch] = useState(false);

    useEffect(() => {
        setIsTouch("ontouchstart" in window || navigator.maxTouchPoints > 0);
    }, []);

    return isTouch;
}
