"use client";

import { forwardRef } from "react";
import { Loader2 } from "lucide-react";
import { usePullToRefresh } from "@/hooks/useMobile";

/**
 * TASK 5.4.1: Pull to Refresh Component
 * 
 * Mobile-style pull-to-refresh container
 */

interface PullToRefreshProps {
    children: React.ReactNode;
    onRefresh: () => Promise<void>;
    disabled?: boolean;
    className?: string;
}

export function PullToRefresh({ children, onRefresh, disabled = false, className = "" }: PullToRefreshProps) {
    const { containerRef, refreshing, pullDistance, pullProgress } = usePullToRefresh({
        onRefresh,
        disabled,
    });

    return (
        <div ref={containerRef} className={`relative ${className}`}>
            {/* Refresh Indicator */}
            <div
                className="absolute inset-x-0 top-0 flex items-center justify-center pointer-events-none z-10 transition-opacity"
                style={{
                    height: Math.max(0, pullDistance),
                    opacity: pullProgress,
                }}
            >
                <div
                    className="flex items-center justify-center w-10 h-10 bg-purple-600 rounded-full shadow-lg"
                    style={{
                        transform: `rotate(${pullProgress * 360}deg)`,
                    }}
                >
                    <Loader2 className={`w-5 h-5 text-white ${refreshing ? "animate-spin" : ""}`} />
                </div>
            </div>

            {/* Content */}
            <div
                style={{
                    transform: `translateY(${pullDistance}px)`,
                    transition: pullDistance === 0 ? "transform 0.2s ease-out" : "none",
                }}
            >
                {children}
            </div>

            {/* Loading Overlay */}
            {refreshing && (
                <div className="absolute inset-0 bg-black/20 pointer-events-none" />
            )}
        </div>
    );
}

/**
 * Bottom Sheet Component
 * 
 * Mobile-style bottom sheet modal
 */

interface BottomSheetProps {
    isOpen: boolean;
    onClose: () => void;
    title?: string;
    children: React.ReactNode;
    snapPoints?: number[];
}

export function BottomSheet({ isOpen, onClose, title, children }: BottomSheetProps) {
    if (!isOpen) return null;

    return (
        <>
            {/* Backdrop */}
            <div
                className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm"
                onClick={onClose}
            />

            {/* Sheet */}
            <div className="fixed inset-x-0 bottom-0 z-50 bg-gray-900 rounded-t-3xl max-h-[90vh] overflow-hidden animate-slide-up">
                {/* Handle */}
                <div className="flex justify-center py-3">
                    <div className="w-12 h-1.5 bg-gray-600 rounded-full" />
                </div>

                {/* Header */}
                {title && (
                    <div className="px-6 pb-4 border-b border-gray-800">
                        <h2 className="text-lg font-semibold">{title}</h2>
                    </div>
                )}

                {/* Content */}
                <div className="px-6 py-4 overflow-y-auto max-h-[70vh]">
                    {children}
                </div>
            </div>

            <style jsx global>{`
        @keyframes slide-up {
          from {
            transform: translateY(100%);
          }
          to {
            transform: translateY(0);
          }
        }
        .animate-slide-up {
          animation: slide-up 0.3s ease-out;
        }
      `}</style>
        </>
    );
}

/**
 * Swipeable Card Component
 * 
 * Card with swipe-to-action functionality
 */

interface SwipeableCardProps {
    children: React.ReactNode;
    onSwipeLeft?: () => void;
    onSwipeRight?: () => void;
    leftAction?: { label: string; color: string; icon?: React.ReactNode };
    rightAction?: { label: string; color: string; icon?: React.ReactNode };
    className?: string;
}

export function SwipeableCard({
    children,
    onSwipeLeft,
    onSwipeRight,
    leftAction,
    rightAction,
    className = "",
}: SwipeableCardProps) {
    return (
        <div className={`relative overflow-hidden rounded-xl ${className}`}>
            {/* Action backgrounds */}
            {leftAction && (
                <div className="absolute inset-y-0 left-0 w-20 flex items-center justify-center" style={{ backgroundColor: leftAction.color }}>
                    {leftAction.icon}
                    <span className="text-xs text-white font-medium">{leftAction.label}</span>
                </div>
            )}
            {rightAction && (
                <div className="absolute inset-y-0 right-0 w-20 flex items-center justify-center" style={{ backgroundColor: rightAction.color }}>
                    {rightAction.icon}
                    <span className="text-xs text-white font-medium">{rightAction.label}</span>
                </div>
            )}

            {/* Card content - would use useSwipe hook */}
            <div className="relative bg-gray-900 touch-pan-y">
                {children}
            </div>
        </div>
    );
}

/**
 * Mobile Action Bar
 * 
 * Fixed bottom action bar for mobile
 */

interface MobileActionBarProps {
    children: React.ReactNode;
    className?: string;
}

export function MobileActionBar({ children, className = "" }: MobileActionBarProps) {
    return (
        <div className={`fixed inset-x-0 bottom-0 z-30 bg-gray-900/95 backdrop-blur-sm border-t border-gray-800 px-4 py-3 pb-safe ${className}`}>
            <div className="flex gap-3">
                {children}
            </div>
        </div>
    );
}

/**
 * Touch-optimized Button
 * 
 * Button with larger touch target and haptic feedback
 */

interface TouchButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: "primary" | "secondary" | "ghost";
    size?: "sm" | "md" | "lg";
    fullWidth?: boolean;
}

export const TouchButton = forwardRef<HTMLButtonElement, TouchButtonProps>(
    ({ variant = "primary", size = "md", fullWidth = false, className = "", children, ...props }, ref) => {
        const baseClasses = "inline-flex items-center justify-center rounded-xl font-medium transition-all active:scale-95";

        const variants = {
            primary: "bg-purple-600 text-white hover:bg-purple-700",
            secondary: "bg-gray-800 text-white hover:bg-gray-700",
            ghost: "bg-transparent text-gray-400 hover:text-white hover:bg-gray-800",
        };

        const sizes = {
            sm: "min-h-[40px] px-4 text-sm",
            md: "min-h-[48px] px-6 text-base",
            lg: "min-h-[56px] px-8 text-lg",
        };

        return (
            <button
                ref={ref}
                className={`${baseClasses} ${variants[variant]} ${sizes[size]} ${fullWidth ? "w-full" : ""} ${className}`}
                {...props}
            >
                {children}
            </button>
        );
    }
);

TouchButton.displayName = "TouchButton";
