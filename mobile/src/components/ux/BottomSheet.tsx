/**
 * Bottom Sheet Component
 *
 * A native-feeling bottom sheet modal with gesture support.
 */

import React, {
  useCallback,
  useEffect,
  useImperativeHandle,
  forwardRef,
} from 'react';
import {
  StyleSheet,
  View,
  Dimensions,
  Modal,
  Pressable,
  ViewStyle,
  Platform,
  StatusBar,
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
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { HapticPresets } from './HapticFeedback';

const { height: SCREEN_HEIGHT, width: SCREEN_WIDTH } = Dimensions.get('window');

export type SnapPoint = number | string; // number for px, string like '50%' for percentage

export interface BottomSheetRef {
  open: () => void;
  close: () => void;
  snapTo: (index: number) => void;
  isOpen: () => boolean;
}

interface BottomSheetProps {
  children: React.ReactNode;
  snapPoints?: SnapPoint[];
  initialSnapIndex?: number;
  enablePanDownToClose?: boolean;
  enableBackdropDismiss?: boolean;
  enableDynamicSizing?: boolean;
  backdropOpacity?: number;
  handleHeight?: number;
  handleStyle?: ViewStyle;
  containerStyle?: ViewStyle;
  onOpen?: () => void;
  onClose?: () => void;
  onChange?: (index: number) => void;
}

function parseSnapPoint(snapPoint: SnapPoint, screenHeight: number): number {
  if (typeof snapPoint === 'number') {
    return snapPoint;
  }
  const percentage = parseFloat(snapPoint) / 100;
  return screenHeight * percentage;
}

export const BottomSheet = forwardRef<BottomSheetRef, BottomSheetProps>(
  (
    {
      children,
      snapPoints = ['50%'],
      initialSnapIndex = 0,
      enablePanDownToClose = true,
      enableBackdropDismiss = true,
      backdropOpacity = 0.5,
      handleHeight = 24,
      handleStyle,
      containerStyle,
      onOpen,
      onClose,
      onChange,
    },
    ref
  ) => {
    const insets = useSafeAreaInsets();
    const isOpen = useSharedValue(false);
    const translateY = useSharedValue(SCREEN_HEIGHT);
    const currentSnapIndex = useSharedValue(initialSnapIndex);

    const statusBarHeight =
      Platform.OS === 'android' ? StatusBar.currentHeight || 0 : 0;
    const availableHeight = SCREEN_HEIGHT - statusBarHeight - insets.top;

    const parsedSnapPoints = snapPoints.map((sp) =>
      parseSnapPoint(sp, availableHeight)
    );

    const getTranslateForSnap = useCallback(
      (index: number) => {
        const snapHeight = parsedSnapPoints[index] || parsedSnapPoints[0];
        return SCREEN_HEIGHT - snapHeight - insets.bottom;
      },
      [parsedSnapPoints, insets.bottom]
    );

    const snapTo = useCallback(
      (index: number) => {
        'worklet';
        currentSnapIndex.value = index;
        translateY.value = withSpring(getTranslateForSnap(index), {
          damping: 25,
          stiffness: 300,
        });
        if (onChange) {
          runOnJS(onChange)(index);
        }
      },
      [translateY, currentSnapIndex, getTranslateForSnap, onChange]
    );

    const open = useCallback(() => {
      isOpen.value = true;
      HapticPresets.sheetOpen();
      translateY.value = withSpring(getTranslateForSnap(initialSnapIndex), {
        damping: 25,
        stiffness: 300,
      });
      if (onOpen) {
        onOpen();
      }
    }, [translateY, getTranslateForSnap, initialSnapIndex, isOpen, onOpen]);

    const close = useCallback(() => {
      HapticPresets.sheetClose();
      translateY.value = withSpring(SCREEN_HEIGHT, {
        damping: 25,
        stiffness: 300,
      });
      setTimeout(() => {
        isOpen.value = false;
        if (onClose) {
          onClose();
        }
      }, 300);
    }, [translateY, isOpen, onClose]);

    useImperativeHandle(ref, () => ({
      open,
      close,
      snapTo: (index: number) => snapTo(index),
      isOpen: () => isOpen.value,
    }));

    const panGesture = Gesture.Pan()
      .onUpdate((event) => {
        const currentTranslate = getTranslateForSnap(currentSnapIndex.value);
        let newTranslate = currentTranslate + event.translationY;

        // Limit upward movement
        const maxSnapHeight = Math.max(...parsedSnapPoints);
        const minTranslate = SCREEN_HEIGHT - maxSnapHeight - insets.bottom;
        newTranslate = Math.max(newTranslate, minTranslate - 50); // Allow slight overshoot

        // Allow downward movement
        if (enablePanDownToClose) {
          newTranslate = Math.min(newTranslate, SCREEN_HEIGHT);
        } else {
          const minSnapHeight = Math.min(...parsedSnapPoints);
          const maxTranslate = SCREEN_HEIGHT - minSnapHeight - insets.bottom;
          newTranslate = Math.min(newTranslate, maxTranslate + 50);
        }

        translateY.value = newTranslate;
      })
      .onEnd((event) => {
        const velocity = event.velocityY;
        const currentTranslate = translateY.value;

        // Fast downward swipe
        if (velocity > 1000 && enablePanDownToClose) {
          runOnJS(close)();
          return;
        }

        // Fast upward swipe
        if (velocity < -1000) {
          const lastIndex = parsedSnapPoints.length - 1;
          snapTo(lastIndex);
          return;
        }

        // Find nearest snap point
        let nearestIndex = 0;
        let minDistance = Infinity;

        parsedSnapPoints.forEach((_, index) => {
          const snapTranslate = getTranslateForSnap(index);
          const distance = Math.abs(currentTranslate - snapTranslate);
          if (distance < minDistance) {
            minDistance = distance;
            nearestIndex = index;
          }
        });

        // Check if should close
        if (enablePanDownToClose) {
          const closeThreshold = getTranslateForSnap(0) + 100;
          if (currentTranslate > closeThreshold) {
            runOnJS(close)();
            return;
          }
        }

        snapTo(nearestIndex);
        runOnJS(HapticPresets.selection)();
      });

    const sheetStyle = useAnimatedStyle(() => {
      return {
        transform: [{ translateY: translateY.value }],
      };
    });

    const backdropStyle = useAnimatedStyle(() => {
      const opacity = interpolate(
        translateY.value,
        [SCREEN_HEIGHT, getTranslateForSnap(0)],
        [0, backdropOpacity],
        Extrapolation.CLAMP
      );

      return {
        opacity,
      };
    });

    if (!isOpen.value && translateY.value >= SCREEN_HEIGHT) {
      return null;
    }

    return (
      <Modal transparent visible statusBarTranslucent animationType="none">
        {/* Backdrop */}
        <Animated.View style={[styles.backdrop, backdropStyle]}>
          <Pressable
            style={styles.backdropPressable}
            onPress={enableBackdropDismiss ? close : undefined}
          />
        </Animated.View>

        {/* Sheet */}
        <GestureDetector gesture={panGesture}>
          <Animated.View style={[styles.sheet, containerStyle, sheetStyle]}>
            {/* Handle */}
            <View style={[styles.handleContainer, { height: handleHeight }]}>
              <View style={[styles.handle, handleStyle]} />
            </View>

            {/* Content */}
            <View style={[styles.content, { paddingBottom: insets.bottom }]}>
              {children}
            </View>
          </Animated.View>
        </GestureDetector>
      </Modal>
    );
  }
);

BottomSheet.displayName = 'BottomSheet';

/**
 * Simple action sheet using BottomSheet
 */
interface ActionSheetAction {
  key: string;
  label: string;
  icon?: React.ReactNode;
  destructive?: boolean;
  onPress: () => void;
}

interface ActionSheetProps {
  visible: boolean;
  onClose: () => void;
  title?: string;
  message?: string;
  actions: ActionSheetAction[];
  cancelLabel?: string;
}

export function ActionSheet({
  visible,
  onClose,
  title,
  message,
  actions,
  cancelLabel = 'Cancel',
}: ActionSheetProps) {
  const sheetRef = React.useRef<BottomSheetRef>(null);

  useEffect(() => {
    if (visible) {
      sheetRef.current?.open();
    } else {
      sheetRef.current?.close();
    }
  }, [visible]);

  const handleAction = (action: ActionSheetAction) => {
    HapticPresets.buttonPress();
    onClose();
    action.onPress();
  };

  return (
    <BottomSheet
      ref={sheetRef}
      snapPoints={['auto']}
      enablePanDownToClose
      enableBackdropDismiss
      onClose={onClose}
    >
      <View style={styles.actionSheet}>
        {title && (
          <View style={styles.actionSheetHeader}>
            <Animated.Text style={styles.actionSheetTitle}>
              {title}
            </Animated.Text>
            {message && (
              <Animated.Text style={styles.actionSheetMessage}>
                {message}
              </Animated.Text>
            )}
          </View>
        )}

        <View style={styles.actionSheetActions}>
          {actions.map((action) => (
            <Pressable
              key={action.key}
              style={styles.actionSheetButton}
              onPress={() => handleAction(action)}
            >
              {action.icon && (
                <View style={styles.actionSheetIcon}>{action.icon}</View>
              )}
              <Animated.Text
                style={[
                  styles.actionSheetButtonText,
                  action.destructive && styles.actionSheetDestructive,
                ]}
              >
                {action.label}
              </Animated.Text>
            </Pressable>
          ))}
        </View>

        <Pressable
          style={[styles.actionSheetButton, styles.actionSheetCancel]}
          onPress={onClose}
        >
          <Animated.Text style={styles.actionSheetCancelText}>
            {cancelLabel}
          </Animated.Text>
        </Pressable>
      </View>
    </BottomSheet>
  );
}

const styles = StyleSheet.create({
  backdrop: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: '#000',
  },
  backdropPressable: {
    flex: 1,
  },
  sheet: {
    position: 'absolute',
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: '#fff',
    borderTopLeftRadius: 16,
    borderTopRightRadius: 16,
    minHeight: 100,
    maxHeight: SCREEN_HEIGHT * 0.9,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: -2,
    },
    shadowOpacity: 0.25,
    shadowRadius: 5,
    elevation: 5,
  },
  handleContainer: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  handle: {
    width: 40,
    height: 4,
    backgroundColor: '#d1d5db',
    borderRadius: 2,
  },
  content: {
    flex: 1,
  },
  actionSheet: {
    paddingHorizontal: 16,
    paddingBottom: 16,
  },
  actionSheetHeader: {
    paddingVertical: 16,
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  actionSheetTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
  },
  actionSheetMessage: {
    fontSize: 14,
    color: '#6b7280',
    marginTop: 4,
    textAlign: 'center',
  },
  actionSheetActions: {
    paddingTop: 8,
  },
  actionSheetButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  actionSheetIcon: {
    marginRight: 12,
  },
  actionSheetButtonText: {
    fontSize: 16,
    color: '#111827',
  },
  actionSheetDestructive: {
    color: '#ef4444',
  },
  actionSheetCancel: {
    marginTop: 8,
    backgroundColor: '#f3f4f6',
    borderRadius: 12,
    borderBottomWidth: 0,
    justifyContent: 'center',
  },
  actionSheetCancelText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#3b82f6',
    textAlign: 'center',
    flex: 1,
  },
});

export default BottomSheet;
