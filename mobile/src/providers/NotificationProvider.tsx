/**
 * NotificationProvider
 *
 * Context provider for push notification state and actions.
 * Wraps the app to provide notification functionality throughout.
 */

import React, { createContext, useContext, ReactNode } from 'react';
import { useNotifications } from '@/hooks/useNotifications';

interface NotificationContextValue {
  token: string | null;
  isRegistered: boolean;
  isLoading: boolean;
  error: string | null;
  badgeCount: number;
  register: () => Promise<void>;
  clearBadge: () => Promise<void>;
  refreshBadgeCount: () => Promise<void>;
}

const NotificationContext = createContext<NotificationContextValue | null>(null);

interface NotificationProviderProps {
  children: ReactNode;
}

export function NotificationProvider({ children }: NotificationProviderProps) {
  const notifications = useNotifications();

  return (
    <NotificationContext.Provider value={notifications}>
      {children}
    </NotificationContext.Provider>
  );
}

export function useNotificationContext(): NotificationContextValue {
  const context = useContext(NotificationContext);

  if (!context) {
    throw new Error(
      'useNotificationContext must be used within a NotificationProvider'
    );
  }

  return context;
}
