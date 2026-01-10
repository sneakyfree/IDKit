"use client";

import { useState, useEffect, useCallback } from "react";

type LiveRegionPoliteness = "polite" | "assertive" | "off";

interface LiveRegionProps {
  politeness?: LiveRegionPoliteness;
  children?: React.ReactNode;
  clearOnUnmount?: boolean;
}

export function LiveRegion({
  politeness = "polite",
  children,
  clearOnUnmount = true,
}: LiveRegionProps) {
  return (
    <div
      role="status"
      aria-live={politeness}
      aria-atomic="true"
      className="sr-only"
    >
      {children}
    </div>
  );
}

// Hook for programmatic announcements
export function useAnnounce() {
  const [message, setMessage] = useState<string>("");
  const [politeness, setPoliteness] =
    useState<LiveRegionPoliteness>("polite");

  const announce = useCallback(
    (newMessage: string, level: LiveRegionPoliteness = "polite") => {
      // Clear first to ensure announcement is read
      setMessage("");
      setPoliteness(level);

      // Set new message after brief delay
      setTimeout(() => {
        setMessage(newMessage);
      }, 50);

      // Clear after announcement
      setTimeout(() => {
        setMessage("");
      }, 5000);
    },
    []
  );

  const announcePolite = useCallback(
    (newMessage: string) => announce(newMessage, "polite"),
    [announce]
  );

  const announceAssertive = useCallback(
    (newMessage: string) => announce(newMessage, "assertive"),
    [announce]
  );

  return {
    announce,
    announcePolite,
    announceAssertive,
    LiveRegion: () => (
      <LiveRegion politeness={politeness}>{message}</LiveRegion>
    ),
  };
}

// Global announcer that can be used anywhere
let globalAnnounce: ((message: string, politeness?: LiveRegionPoliteness) => void) | null = null;

export function setGlobalAnnouncer(
  announcer: (message: string, politeness?: LiveRegionPoliteness) => void
) {
  globalAnnounce = announcer;
}

export function announceToScreenReader(
  message: string,
  politeness: LiveRegionPoliteness = "polite"
) {
  if (globalAnnounce) {
    globalAnnounce(message, politeness);
  }
}

export function GlobalLiveRegion() {
  const { announce, LiveRegion } = useAnnounce();

  useEffect(() => {
    setGlobalAnnouncer(announce);
    return () => {
      globalAnnounce = null;
    };
  }, [announce]);

  return <LiveRegion />;
}

export default LiveRegion;
