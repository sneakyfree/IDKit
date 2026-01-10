/**
 * Swipeable Row Component
 *
 * A row component that supports swipe gestures to reveal
 * action buttons (like delete, archive, etc.)
 */

import React, { useCallback, useRef } from 'react';
import {
  StyleSheet,
  View,
  Text,
  Pressable,
  Dimensions,
  ViewStyle,
} from 'react-native';
import { Gesture, GestureDetector } from 'react-native-gesture-handler';
import Animated, {
  useAnimatedStyle,
  useSharedValue,
  withSpring,
  withTiming,
  runOnJS,
  interpolate,
  Extrapolation,
} from 'react-native-reanimated';
import { HapticPresets } from './HapticFeedback';

const { width: SCREEN_WIDTH } = Dimensions.get('window');
const ACTION_WIDTH = 80;

export interface SwipeAction {
  key: string;
  label: string;
  icon?: React.ReactNode;
  backgroundColor: string;
  textColor?: string;
  onPress: () => void;
  confirmText?: string;
}

interface SwipeableRowProps {
  children: React.ReactNode;
  leftActions?: SwipeAction[];
  rightActions?: SwipeAction[];
  swipeThreshold?: number;
  overshootLeft?: boolean;
  overshootRight?: boolean;
  friction?: number;
  onSwipeStart?: () => void;
  onSwipeEnd?: () => void;
  style?: ViewStyle;
  enabled?: boolean;
}

export function SwipeableRow({
  children,
  leftActions = [],
  rightActions = [],
  swipeThreshold = 0.5,
  overshootLeft = true,
  overshootRight = true,
  friction = 1,
  onSwipeStart,
  onSwipeEnd,
  style,
  enabled = true,
}: SwipeableRowProps) {
  const translateX = useSharedValue(0);
  const isOpen = useSharedValue(false);
  const activeAction = useSharedValue<string | null>(null);

  const leftWidth = leftActions.length * ACTION_WIDTH;
  const rightWidth = rightActions.length * ACTION_WIDTH;

  const close = useCallback(() => {
    'worklet';
    translateX.value = withSpring(0, {
      damping: 20,
      stiffness: 200,
    });
    isOpen.value = false;
    activeAction.value = null;
  }, [translateX, isOpen, activeAction]);

  const openLeft = useCallback(() => {
    'worklet';
    translateX.value = withSpring(leftWidth, {
      damping: 20,
      stiffness: 200,
    });
    isOpen.value = true;
    runOnJS(HapticPresets.swipeAction)();
  }, [translateX, leftWidth, isOpen]);

  const openRight = useCallback(() => {
    'worklet';
    translateX.value = withSpring(-rightWidth, {
      damping: 20,
      stiffness: 200,
    });
    isOpen.value = true;
    runOnJS(HapticPresets.swipeAction)();
  }, [translateX, rightWidth, isOpen]);

  const panGesture = Gesture.Pan()
    .enabled(enabled)
    .onStart(() => {
      if (onSwipeStart) {
        runOnJS(onSwipeStart)();
      }
    })
    .onUpdate((event) => {
      let newValue = event.translationX / friction;

      // Add current open position
      if (isOpen.value) {
        if (translateX.value > 0) {
          newValue += leftWidth;
        } else {
          newValue -= rightWidth;
        }
      }

      // Limit swipe distance
      const maxLeft = overshootLeft ? leftWidth + 20 : leftWidth;
      const maxRight = overshootRight ? rightWidth + 20 : rightWidth;

      if (newValue > 0) {
        // Swiping right (revealing left actions)
        if (leftActions.length === 0) {
          newValue = 0;
        } else {
          newValue = Math.min(newValue, maxLeft);
        }
      } else {
        // Swiping left (revealing right actions)
        if (rightActions.length === 0) {
          newValue = 0;
        } else {
          newValue = Math.max(newValue, -maxRight);
        }
      }

      translateX.value = newValue;
    })
    .onEnd((event) => {
      if (onSwipeEnd) {
        runOnJS(onSwipeEnd)();
      }

      const velocity = event.velocityX;
      const threshold = swipeThreshold;

      if (translateX.value > 0) {
        // Revealing left actions
        if (translateX.value > leftWidth * threshold || velocity > 500) {
          openLeft();
        } else {
          close();
        }
      } else {
        // Revealing right actions
        if (
          Math.abs(translateX.value) > rightWidth * threshold ||
          velocity < -500
        ) {
          openRight();
        } else {
          close();
        }
      }
    });

  const contentStyle = useAnimatedStyle(() => {
    return {
      transform: [{ translateX: translateX.value }],
    };
  });

  const leftActionsStyle = useAnimatedStyle(() => {
    return {
      width: Math.max(0, translateX.value),
    };
  });

  const rightActionsStyle = useAnimatedStyle(() => {
    return {
      width: Math.max(0, -translateX.value),
    };
  });

  const renderAction = (
    action: SwipeAction,
    index: number,
    side: 'left' | 'right'
  ) => {
    const handlePress = () => {
      HapticPresets.buttonPress();
      action.onPress();
      close();
    };

    return (
      <Pressable
        key={action.key}
        onPress={handlePress}
        style={[
          styles.action,
          {
            backgroundColor: action.backgroundColor,
            width: ACTION_WIDTH,
          },
        ]}
      >
        {action.icon}
        <Text
          style={[styles.actionText, { color: action.textColor || '#fff' }]}
        >
          {action.label}
        </Text>
      </Pressable>
    );
  };

  return (
    <View style={[styles.container, style]}>
      {/* Left actions (revealed when swiping right) */}
      {leftActions.length > 0 && (
        <Animated.View style={[styles.actionsContainer, styles.leftActions, leftActionsStyle]}>
          <View style={styles.actionsRow}>
            {leftActions.map((action, index) => renderAction(action, index, 'left'))}
          </View>
        </Animated.View>
      )}

      {/* Right actions (revealed when swiping left) */}
      {rightActions.length > 0 && (
        <Animated.View style={[styles.actionsContainer, styles.rightActions, rightActionsStyle]}>
          <View style={styles.actionsRow}>
            {rightActions.map((action, index) => renderAction(action, index, 'right'))}
          </View>
        </Animated.View>
      )}

      {/* Main content */}
      <GestureDetector gesture={panGesture}>
        <Animated.View style={[styles.content, contentStyle]}>
          {children}
        </Animated.View>
      </GestureDetector>
    </View>
  );
}

/**
 * Pre-configured swipeable row for delete actions
 */
interface SwipeToDeleteRowProps {
  children: React.ReactNode;
  onDelete: () => void;
  deleteLabel?: string;
  confirmDelete?: boolean;
  style?: ViewStyle;
}

export function SwipeToDeleteRow({
  children,
  onDelete,
  deleteLabel = 'Delete',
  confirmDelete = false,
  style,
}: SwipeToDeleteRowProps) {
  const rightActions: SwipeAction[] = [
    {
      key: 'delete',
      label: deleteLabel,
      backgroundColor: '#ef4444',
      textColor: '#fff',
      onPress: () => {
        HapticPresets.swipeDelete();
        onDelete();
      },
    },
  ];

  return (
    <SwipeableRow rightActions={rightActions} style={style}>
      {children}
    </SwipeableRow>
  );
}

/**
 * Pre-configured swipeable row for archive/unread actions
 */
interface SwipeToArchiveRowProps {
  children: React.ReactNode;
  onArchive: () => void;
  onMarkUnread?: () => void;
  archiveLabel?: string;
  unreadLabel?: string;
  style?: ViewStyle;
}

export function SwipeToArchiveRow({
  children,
  onArchive,
  onMarkUnread,
  archiveLabel = 'Archive',
  unreadLabel = 'Unread',
  style,
}: SwipeToArchiveRowProps) {
  const rightActions: SwipeAction[] = [
    {
      key: 'archive',
      label: archiveLabel,
      backgroundColor: '#6b7280',
      onPress: onArchive,
    },
  ];

  const leftActions: SwipeAction[] = onMarkUnread
    ? [
        {
          key: 'unread',
          label: unreadLabel,
          backgroundColor: '#3b82f6',
          onPress: onMarkUnread,
        },
      ]
    : [];

  return (
    <SwipeableRow
      leftActions={leftActions}
      rightActions={rightActions}
      style={style}
    >
      {children}
    </SwipeableRow>
  );
}

const styles = StyleSheet.create({
  container: {
    overflow: 'hidden',
    position: 'relative',
  },
  content: {
    backgroundColor: '#fff',
  },
  actionsContainer: {
    position: 'absolute',
    top: 0,
    bottom: 0,
    overflow: 'hidden',
  },
  leftActions: {
    left: 0,
  },
  rightActions: {
    right: 0,
  },
  actionsRow: {
    flexDirection: 'row',
    height: '100%',
  },
  action: {
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 16,
  },
  actionText: {
    fontSize: 12,
    fontWeight: '600',
    marginTop: 4,
  },
});

export default SwipeableRow;
