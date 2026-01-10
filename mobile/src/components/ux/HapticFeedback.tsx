/**
 * Haptic Feedback Utilities
 *
 * Provides haptic feedback for user interactions to create
 * a more native and responsive feel.
 */

import { useCallback } from 'react';
import * as Haptics from 'expo-haptics';
import { Platform } from 'react-native';

/**
 * Haptic feedback types for different interactions
 */
export type HapticType =
  | 'light'
  | 'medium'
  | 'heavy'
  | 'success'
  | 'warning'
  | 'error'
  | 'selection';

/**
 * Trigger haptic feedback
 */
export async function triggerHaptic(type: HapticType = 'light'): Promise<void> {
  // Only trigger haptics on native platforms
  if (Platform.OS === 'web') {
    return;
  }

  try {
    switch (type) {
      case 'light':
        await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
        break;
      case 'medium':
        await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
        break;
      case 'heavy':
        await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Heavy);
        break;
      case 'success':
        await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
        break;
      case 'warning':
        await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning);
        break;
      case 'error':
        await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
        break;
      case 'selection':
        await Haptics.selectionAsync();
        break;
      default:
        await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    }
  } catch (error) {
    // Silently fail if haptics not available
    console.debug('Haptic feedback not available:', error);
  }
}

/**
 * Hook for haptic feedback
 */
export function useHaptic(type: HapticType = 'light') {
  const trigger = useCallback(() => {
    triggerHaptic(type);
  }, [type]);

  return trigger;
}

/**
 * Create a press handler with haptic feedback
 */
export function withHaptic<T extends (...args: any[]) => any>(
  handler: T,
  type: HapticType = 'light'
): T {
  return ((...args: Parameters<T>) => {
    triggerHaptic(type);
    return handler(...args);
  }) as T;
}

/**
 * Common haptic presets for specific interactions
 */
export const HapticPresets = {
  // Button presses
  buttonPress: () => triggerHaptic('light'),
  buttonPressHeavy: () => triggerHaptic('medium'),

  // Tab/selection changes
  tabChange: () => triggerHaptic('selection'),
  menuSelect: () => triggerHaptic('selection'),

  // Toggle switches
  toggleOn: () => triggerHaptic('light'),
  toggleOff: () => triggerHaptic('light'),

  // Like/favorite actions
  like: () => triggerHaptic('medium'),
  unlike: () => triggerHaptic('light'),

  // Success/error states
  success: () => triggerHaptic('success'),
  error: () => triggerHaptic('error'),
  warning: () => triggerHaptic('warning'),

  // Pull to refresh
  refreshStart: () => triggerHaptic('medium'),
  refreshComplete: () => triggerHaptic('success'),

  // Swipe actions
  swipeAction: () => triggerHaptic('medium'),
  swipeDelete: () => triggerHaptic('heavy'),

  // Modal/sheet interactions
  sheetOpen: () => triggerHaptic('medium'),
  sheetClose: () => triggerHaptic('light'),

  // Drag and drop
  dragStart: () => triggerHaptic('medium'),
  dragEnd: () => triggerHaptic('light'),
  dropSuccess: () => triggerHaptic('success'),

  // Long press
  longPressStart: () => triggerHaptic('heavy'),

  // Slider interactions
  sliderTick: () => triggerHaptic('selection'),
  sliderEnd: () => triggerHaptic('light'),
};

export default {
  trigger: triggerHaptic,
  useHaptic,
  withHaptic,
  presets: HapticPresets,
};
