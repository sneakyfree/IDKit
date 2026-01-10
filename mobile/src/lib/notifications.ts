/**
 * Push Notifications Service
 *
 * Handles push notification registration, permissions, and handling.
 * Uses Expo Notifications for cross-platform support.
 */

import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import { Platform } from 'react-native';
import Constants from 'expo-constants';

// Configure notification behavior
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
  }),
});

export type NotificationData = {
  type: 'comment' | 'like' | 'follow' | 'mention' | 'message' | 'content_ready' | 'campaign';
  title: string;
  body: string;
  data?: Record<string, unknown>;
};

/**
 * Register for push notifications and get the token.
 */
export async function registerForPushNotifications(): Promise<string | null> {
  let token: string | null = null;

  // Push notifications only work on physical devices
  if (!Device.isDevice) {
    console.warn('Push notifications only work on physical devices');
    return null;
  }

  // Check existing permissions
  const { status: existingStatus } = await Notifications.getPermissionsAsync();
  let finalStatus = existingStatus;

  // Request permissions if not granted
  if (existingStatus !== 'granted') {
    const { status } = await Notifications.requestPermissionsAsync();
    finalStatus = status;
  }

  if (finalStatus !== 'granted') {
    console.warn('Push notification permission denied');
    return null;
  }

  // Get the Expo push token
  try {
    const projectId = Constants.expoConfig?.extra?.eas?.projectId;
    const tokenData = await Notifications.getExpoPushTokenAsync({
      projectId,
    });
    token = tokenData.data;
  } catch (error) {
    console.error('Failed to get push token:', error);
    return null;
  }

  // Android-specific channel configuration
  if (Platform.OS === 'android') {
    await setupAndroidChannels();
  }

  return token;
}

/**
 * Set up notification channels for Android.
 */
async function setupAndroidChannels(): Promise<void> {
  // Default channel for general notifications
  await Notifications.setNotificationChannelAsync('default', {
    name: 'Default',
    importance: Notifications.AndroidImportance.HIGH,
    vibrationPattern: [0, 250, 250, 250],
    lightColor: '#8B5CF6',
    sound: 'default',
  });

  // Channel for social interactions (likes, comments, follows)
  await Notifications.setNotificationChannelAsync('social', {
    name: 'Social',
    description: 'Likes, comments, and new followers',
    importance: Notifications.AndroidImportance.HIGH,
    vibrationPattern: [0, 250, 250, 250],
    lightColor: '#EC4899',
    sound: 'default',
  });

  // Channel for messages
  await Notifications.setNotificationChannelAsync('messages', {
    name: 'Messages',
    description: 'Direct messages',
    importance: Notifications.AndroidImportance.MAX,
    vibrationPattern: [0, 250, 250, 250],
    lightColor: '#3B82F6',
    sound: 'default',
  });

  // Channel for content generation
  await Notifications.setNotificationChannelAsync('content', {
    name: 'Content',
    description: 'Content generation and publishing updates',
    importance: Notifications.AndroidImportance.DEFAULT,
    vibrationPattern: [0, 250],
    lightColor: '#22C55E',
    sound: 'default',
  });

  // Channel for campaigns
  await Notifications.setNotificationChannelAsync('campaigns', {
    name: 'Campaigns',
    description: 'Email and SMS campaign updates',
    importance: Notifications.AndroidImportance.DEFAULT,
    vibrationPattern: [0, 250],
    lightColor: '#F97316',
    sound: 'default',
  });
}

/**
 * Schedule a local notification.
 */
export async function scheduleLocalNotification(
  notification: NotificationData,
  trigger?: Notifications.NotificationTriggerInput
): Promise<string> {
  const channelId = getChannelForType(notification.type);

  return await Notifications.scheduleNotificationAsync({
    content: {
      title: notification.title,
      body: notification.body,
      data: {
        type: notification.type,
        ...notification.data,
      },
      sound: 'default',
      ...(Platform.OS === 'android' && { channelId }),
    },
    trigger: trigger ?? null,
  });
}

/**
 * Get the appropriate channel for a notification type.
 */
function getChannelForType(type: NotificationData['type']): string {
  switch (type) {
    case 'comment':
    case 'like':
    case 'follow':
    case 'mention':
      return 'social';
    case 'message':
      return 'messages';
    case 'content_ready':
      return 'content';
    case 'campaign':
      return 'campaigns';
    default:
      return 'default';
  }
}

/**
 * Cancel all scheduled notifications.
 */
export async function cancelAllNotifications(): Promise<void> {
  await Notifications.cancelAllScheduledNotificationsAsync();
}

/**
 * Cancel a specific notification.
 */
export async function cancelNotification(notificationId: string): Promise<void> {
  await Notifications.cancelScheduledNotificationAsync(notificationId);
}

/**
 * Get the badge count.
 */
export async function getBadgeCount(): Promise<number> {
  return await Notifications.getBadgeCountAsync();
}

/**
 * Set the badge count.
 */
export async function setBadgeCount(count: number): Promise<void> {
  await Notifications.setBadgeCountAsync(count);
}

/**
 * Clear all delivered notifications.
 */
export async function clearAllDeliveredNotifications(): Promise<void> {
  await Notifications.dismissAllNotificationsAsync();
}

/**
 * Add a listener for received notifications (when app is in foreground).
 */
export function addNotificationReceivedListener(
  callback: (notification: Notifications.Notification) => void
): Notifications.Subscription {
  return Notifications.addNotificationReceivedListener(callback);
}

/**
 * Add a listener for notification responses (when user taps notification).
 */
export function addNotificationResponseListener(
  callback: (response: Notifications.NotificationResponse) => void
): Notifications.Subscription {
  return Notifications.addNotificationResponseReceivedListener(callback);
}

/**
 * Get the last notification response (for deep linking on app launch).
 */
export async function getLastNotificationResponse(): Promise<Notifications.NotificationResponse | null> {
  return await Notifications.getLastNotificationResponseAsync();
}
