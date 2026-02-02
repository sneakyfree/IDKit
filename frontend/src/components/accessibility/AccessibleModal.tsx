"use client";

import React, { useEffect } from "react";
import { useFocusTrap, useReturnFocus, ariaPatterns, generateAriaId } from "@/lib/accessibility";

interface AccessibleModalProps {
    isOpen: boolean;
    onClose: () => void;
    title: string;
    children: React.ReactNode;
    size?: "sm" | "md" | "lg" | "xl" | "full";
    closeOnOverlayClick?: boolean;
    closeOnEscape?: boolean;
}

/**
 * AccessibleModal - WCAG 2.1 AA compliant modal dialog
 * 
 * Features:
 * - Focus trapping
 * - Returns focus on close
 * - Escape key to close
 * - Proper ARIA attributes
 * - Background scroll lock
 */
export function AccessibleModal({
    isOpen,
    onClose,
    title,
    children,
    size = "md",
    closeOnOverlayClick = true,
    closeOnEscape = true,
}: AccessibleModalProps) {
    const containerRef = useFocusTrap(isOpen);
    useReturnFocus();

    const titleId = React.useMemo(() => generateAriaId("modal-title"), []);

    // Handle escape key
    useEffect(() => {
        if (!isOpen || !closeOnEscape) return;

        const handleEscape = (e: KeyboardEvent) => {
            if (e.key === "Escape") {
                onClose();
            }
        };

        document.addEventListener("keydown", handleEscape);
        return () => document.removeEventListener("keydown", handleEscape);
    }, [isOpen, closeOnEscape, onClose]);

    // Lock body scroll when open
    useEffect(() => {
        if (isOpen) {
            document.body.style.overflow = "hidden";
        } else {
            document.body.style.overflow = "";
        }

        return () => {
            document.body.style.overflow = "";
        };
    }, [isOpen]);

    if (!isOpen) return null;

    const sizeClasses = {
        sm: "max-w-sm",
        md: "max-w-md",
        lg: "max-w-lg",
        xl: "max-w-xl",
        full: "max-w-full mx-4",
    };

    return (
        <div
            className="fixed inset-0 z-50 flex items-center justify-center"
            {...ariaPatterns.dialog(titleId)}
        >
            {/* Overlay */}
            <div
                className="absolute inset-0 bg-black/80 backdrop-blur-sm"
                onClick={closeOnOverlayClick ? onClose : undefined}
                aria-hidden="true"
            />

            {/* Modal container */}
            <div
                ref={containerRef}
                className={`relative bg-gray-900 rounded-2xl shadow-xl w-full ${sizeClasses[size]} max-h-[90vh] overflow-auto`}
                role="document"
            >
                {/* Header */}
                <div className="flex items-center justify-between p-4 border-b border-gray-800">
                    <h2 id={titleId} className="text-xl font-semibold">
                        {title}
                    </h2>
                    <button
                        onClick={onClose}
                        className="p-2 text-gray-400 hover:text-white rounded-lg hover:bg-gray-800 transition-colors"
                        aria-label="Close modal"
                    >
                        <svg
                            className="w-5 h-5"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                        >
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M6 18L18 6M6 6l12 12"
                            />
                        </svg>
                    </button>
                </div>

                {/* Content */}
                <div className="p-4">{children}</div>
            </div>
        </div>
    );
}

/**
 * AccessibleAlertDialog - For confirmations and critical actions
 */
export function AccessibleAlertDialog({
    isOpen,
    onClose,
    onConfirm,
    title,
    message,
    confirmLabel = "Confirm",
    cancelLabel = "Cancel",
    variant = "danger",
}: {
    isOpen: boolean;
    onClose: () => void;
    onConfirm: () => void;
    title: string;
    message: string;
    confirmLabel?: string;
    cancelLabel?: string;
    variant?: "danger" | "warning" | "info";
}) {
    const containerRef = useFocusTrap(isOpen);
    useReturnFocus();

    const titleId = React.useMemo(() => generateAriaId("alert-title"), []);
    const descId = React.useMemo(() => generateAriaId("alert-desc"), []);

    useEffect(() => {
        if (!isOpen) return;

        const handleEscape = (e: KeyboardEvent) => {
            if (e.key === "Escape") onClose();
        };

        document.addEventListener("keydown", handleEscape);
        return () => document.removeEventListener("keydown", handleEscape);
    }, [isOpen, onClose]);

    if (!isOpen) return null;

    const variantStyles = {
        danger: "bg-red-600 hover:bg-red-700",
        warning: "bg-yellow-600 hover:bg-yellow-700",
        info: "bg-blue-600 hover:bg-blue-700",
    };

    return (
        <div
            className="fixed inset-0 z-50 flex items-center justify-center"
            role="alertdialog"
            aria-modal="true"
            aria-labelledby={titleId}
            aria-describedby={descId}
        >
            <div className="absolute inset-0 bg-black/80" aria-hidden="true" />

            <div
                ref={containerRef}
                className="relative bg-gray-900 rounded-2xl shadow-xl w-full max-w-sm p-6"
            >
                <h2 id={titleId} className="text-xl font-semibold mb-2">
                    {title}
                </h2>
                <p id={descId} className="text-gray-400 mb-6">
                    {message}
                </p>

                <div className="flex gap-3">
                    <button
                        onClick={onClose}
                        className="flex-1 py-2.5 border border-gray-700 rounded-xl font-medium hover:bg-gray-800 transition-colors"
                    >
                        {cancelLabel}
                    </button>
                    <button
                        onClick={() => {
                            onConfirm();
                            onClose();
                        }}
                        className={`flex-1 py-2.5 rounded-xl font-medium text-white transition-colors ${variantStyles[variant]}`}
                    >
                        {confirmLabel}
                    </button>
                </div>
            </div>
        </div>
    );
}

export default AccessibleModal;
