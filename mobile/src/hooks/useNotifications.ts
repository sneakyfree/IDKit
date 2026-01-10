/**
 * useNotifications Hook
 *
 * React hook for managing push notifications in the app.
 * Handles registration, listeners, and navigation.
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import { useRouter } from 'expo-router';
import * as Notifications from 'expo-notifications';

import {
  registerForPushNotifications,
  addNotificationReceivedListener,
  addNotificationResponseListener,
  getLastNotificationResponse,
  setBadgeCount,
  getBadgeCount,
} from '@/lib/notifications';
import { api } from '@/lib/api';

type NotificationType =
  | 'comment'
  | 'like'
  | 'follow'
  | 'mention'
  | 'message'
  | 'content_ready'
  | 'campaign';

interface NotificationState {
  token: string | null;
  isRegistered: boolean;
  isLoading: boolean;
  error: string | null;
  badgeCount: number;
}

export function useNotifications() {
  const router = useRouter();
  const [state, setState] = useState<NotificationState>({
    token: null,
    isRegistered: false,
    isLoading: true,
    error: null,
    badgeCount: 0,
  });

  // Refs for subscription cleanup
  const notificationListener = useRef<Notifications.Subscription>();
  const responseListener = useRef<Notifications.Subscription>();

  /**
   * Register device for push notifications.
   */
  const register = useCallback(async () => {
    setState((prev) => ({ ...prev, isLoading: true, error: null }));

    try {
      const token = await registerForPushNotifications();

      if (token) {
        // Send token to backend
        await api.post('/v1/notifications/register', {
          token,
          platform: 'expo',
        });

        setState((prev) => ({
          ...prev,
          token,
          isRegistered: true,
          isLoading: false,
        }));
      } else {
        setState((prev) => ({
          ...prev,
          isLoading: false,
          error: 'Failed to get push token',
        }));
      }
    } catch (error) {
      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: 'Failed to register for notifications',
      }));
    }
  }, []);

  /**
   * Handle notification received while app is in foreground.
   */
  const handleNotificationReceived = useCallback(
    (notification: Notifications.Notification) => {
      // Update badge count
      getBadgeCount().then((count) => {
        setState((prev) => ({ ...prev, badgeCount: count + 1 }));
        setBadgeCount(count + 1);
      });

      // You can add custom handling here (e.g., show in-app toast)
      console.log('Notification received:', notification);
    },
    []
  );

  /**
   * Handle notification response (user tapped notification).
   */
  const handleNotificationResponse = useCallback(
    (response: Notifications.NotificationResponse) => {
      const data = response.notification.request.content.data;
      const type = data?.type as NotificationType;

      // Navigate based on notification type
      switch (type) {
        case 'comment':
        case 'like':
        case 'mention':
          if (data?.postId) {
            router.push(`/posts/${data.postId}`);
          } else {
            router.push('/(tabs)/inbox');
          }
          break;

        case 'follow':
          if (data?.userId) {
            router.push(`/profile/${data.userId}`);
          } else {
            router.push('/(tabs)/inbox');
          }
          break;

        case 'message':
          if (data?.conversationId) {
            router.push(`/messages/${data.conversationId}`);
          } else {
            router.push('/(tabs)/inbox');
          }
          break;

        case 'content_ready':
          if (data?.contentId) {
            router.push(`/studio/edit/${data.contentId}`);
          } else {
            router.push('/studio');
          }
          break;

        case 'campaign':
          if (data?.campaignId) {
            router.push(`/campaigns/${data.campaignId}`);
          }
          break;

        default:
          router.push('/(tabs)/inbox');
      }
    },
    [router]
  );

  /**
   * Clear badge count.
   */
  const clearBadge = useCallback(async () => {
    await setBadgeCount(0);
    setState((prev) => ({ ...prev, badgeCount: 0 }));
  }, []);

  /**
   * Refresh badge count from server.
   */
  const refreshBadgeCount = useCallback(async () => {
    try {
      const response = await api.get('/v1/notifications/unread-count');
      const count = response.data?.count ?? 0;
      await setBadgeCount(count);
      setState((prev) => ({ ...prev, badgeCount: count }));
    } catch (error) {
      console.error('Failed to refresh badge count:', error);
    }
  }, []);

  // Initialize notifications on mount
  useEffect(() => {
    register();

    // Check for notification that launched the app
    getLastNotificationResponse().then((response) => {
      if (response) {
        handleNotificationResponse(response);
      }
    });

    // Set up listeners
    notificationListener.current = addNotificationReceivedListener(
      handleNotificationReceived
    );
    responseListener.current = addNotificationResponseListener(
      handleNotificationResponse
    );

    // Get initial badge count
    getBadgeCount().then((count) => {
      setState((prev) => ({ ...prev, badgeCount: count }));
    });

    // Cleanup on unmount
    return () => {
      if (notificationListener.current) {
        notificationListener.current.remove();
      }
      if (responseListener.current) {
        responseListener.current.remove();
      }
    };
  }, [register, handleNotificationReceived, handleNotificationResponse]);

  return {
    ...state,
    register,
    clearBadge,
    refreshBadgeCount,
  };
}
