/**
 * Gesture Navigation
 *
 * Provides swipe-to-go-back and other gesture-based
 * navigation patterns for a more native feel.
 */

import React, { createContext, useContext, useCallback, useRef } from 'react';
import {
  StyleSheet,
  View,
  Dimensions,
  Platform,
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
import { useRouter } from 'expo-router';
import { HapticPresets } from './HapticFeedback';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

/**
 * Swipe back threshold (percentage of screen width)
 */
const SWIPE_THRESHOLD = 0.35;

/**
 * Context for swipe back functionality
 */
interface SwipeBackContextType {
  enabled: boolean;
  setEnabled: (enabled: boolean) => void;
}

const SwipeBackContext = createContext<SwipeBackContextType>({
  enabled: true,
  setEnabled: () => {},
});

/**
 * Provider for swipe back functionality
 */
interface SwipeBackProviderProps {
  children: React.ReactNode;
  enabled?: boolean;
}

export function SwipeBackProvider({
  children,
  enabled: initialEnabled = true,
}: SwipeBackProviderProps) {
  const [enabled, setEnabled] = React.useState(initialEnabled);

  return (
    <SwipeBackContext.Provider value={{ enabled, setEnabled }}>
      {children}
    </SwipeBackContext.Provider>
  );
}

/**
 * Hook for swipe back functionality
 */
export function useSwipeBack() {
  const context = useContext(SwipeBackContext);
  const router = useRouter();

  const goBack = useCallback(() => {
    if (router.canGoBack()) {
      HapticPresets.buttonPress();
      router.back();
    }
  }, [router]);

  return {
    ...context,
    goBack,
    canGoBack: router.canGoBack(),
  };
}

/**
 * Swipe back gesture wrapper
 */
interface SwipeBackViewProps {
  children: React.ReactNode;
  enabled?: boolean;
  onSwipeBack?: () => void;
}

export function SwipeBackView({
  children,
  enabled = true,
  onSwipeBack,
}: SwipeBackViewProps) {
  const router = useRouter();
  const translateX = useSharedValue(0);
  const isActive = useSharedValue(false);

  const handleBack = useCallback(() => {
    if (onSwipeBack) {
      onSwipeBack();
    } else if (router.canGoBack()) {
      HapticPresets.buttonPress();
      router.back();
    }
  }, [router, onSwipeBack]);

  const panGesture = Gesture.Pan()
    .enabled(enabled)
    .activeOffsetX(15) // Only activate for horizontal swipes
    .failOffsetY([-15, 15]) // Fail for vertical movement
    .onStart((event) => {
      // Only activate if starting from left edge
      if (event.x < 30) {
        isActive.value = true;
      }
    })
    .onUpdate((event) => {
      if (!isActive.value) return;

      // Only allow right swipe
      if (event.translationX > 0) {
        translateX.value = event.translationX;
      }
    })
    .onEnd((event) => {
      if (!isActive.value) {
        return;
      }

      isActive.value = false;

      // Check if swipe was far enough
      if (translateX.value > SCREEN_WIDTH * SWIPE_THRESHOLD) {
        // Complete the swipe
        translateX.value = withTiming(SCREEN_WIDTH, { duration: 200 }, () => {
          runOnJS(handleBack)();
        });
      } else {
        // Snap back
        translateX.value = withSpring(0, {
          damping: 20,
          stiffness: 300,
        });
      }
    });

  const animatedStyle = useAnimatedStyle(() => {
    return {
      transform: [{ translateX: translateX.value }],
    };
  });

  const shadowStyle = useAnimatedStyle(() => {
    const opacity = interpolate(
      translateX.value,
      [0, SCREEN_WIDTH],
      [0, 0.3],
      Extrapolation.CLAMP
    );

    return {
      opacity,
    };
  });

  const edgeIndicatorStyle = useAnimatedStyle(() => {
    const opacity = interpolate(
      translateX.value,
      [0, 50],
      [0, 1],
      Extrapolation.CLAMP
    );
    const translateXValue = interpolate(
      translateX.value,
      [0, 100],
      [-20, 0],
      Extrapolation.CLAMP
    );

    return {
      opacity,
      transform: [{ translateX: translateXValue }],
    };
  });

  // Skip gesture handling on iOS where native gestures work well
  if (Platform.OS === 'ios') {
    return <View style={styles.container}>{children}</View>;
  }

  return (
    <View style={styles.container}>
      {/* Shadow overlay */}
      <Animated.View
        style={[styles.shadow, shadowStyle]}
        pointerEvents="none"
      />

      {/* Edge indicator */}
      <Animated.View style={[styles.edgeIndicator, edgeIndicatorStyle]}>
        <View style={styles.edgeArrow} />
      </Animated.View>

      {/* Content */}
      <GestureDetector gesture={panGesture}>
        <Animated.View style={[styles.content, animatedStyle]}>
          {children}
        </Animated.View>
      </GestureDetector>
    </View>
  );
}

/**
 * Edge swipe indicator component
 */
function EdgeSwipeIndicator({
  side = 'left',
  visible = false,
}: {
  side?: 'left' | 'right';
  visible?: boolean;
}) {
  const opacity = useSharedValue(visible ? 1 : 0);

  React.useEffect(() => {
    opacity.value = withTiming(visible ? 1 : 0, { duration: 150 });
  }, [visible, opacity]);

  const animatedStyle = useAnimatedStyle(() => ({
    opacity: opacity.value,
  }));

  return (
    <Animated.View
      style={[
        styles.swipeIndicator,
        side === 'left' ? styles.swipeIndicatorLeft : styles.swipeIndicatorRight,
        animatedStyle,
      ]}
    >
      <View
        style={[
          styles.swipeIndicatorArrow,
          side === 'left'
            ? styles.swipeIndicatorArrowLeft
            : styles.swipeIndicatorArrowRight,
        ]}
      />
    </Animated.View>
  );
}

/**
 * Hook for detecting edge swipes
 */
export function useEdgeSwipe(
  side: 'left' | 'right',
  onSwipe: () => void,
  threshold: number = 50
) {
  const startX = useRef<number | null>(null);

  const handleTouchStart = useCallback((event: any) => {
    const x = event.nativeEvent.pageX;
    if (side === 'left' && x < 30) {
      startX.current = x;
    } else if (side === 'right' && x > SCREEN_WIDTH - 30) {
      startX.current = x;
    }
  }, [side]);

  const handleTouchMove = useCallback((event: any) => {
    if (startX.current === null) return;

    const x = event.nativeEvent.pageX;
    const delta = side === 'left' ? x - startX.current : startX.current - x;

    if (delta > threshold) {
      startX.current = null;
      onSwipe();
    }
  }, [side, threshold, onSwipe]);

  const handleTouchEnd = useCallback(() => {
    startX.current = null;
  }, []);

  return {
    onTouchStart: handleTouchStart,
    onTouchMove: handleTouchMove,
    onTouchEnd: handleTouchEnd,
    onTouchCancel: handleTouchEnd,
  };
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    overflow: 'hidden',
  },
  content: {
    flex: 1,
    backgroundColor: '#fff',
  },
  shadow: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: '#000',
    zIndex: 1,
  },
  edgeIndicator: {
    position: 'absolute',
    left: 0,
    top: '50%',
    width: 24,
    height: 48,
    marginTop: -24,
    backgroundColor: 'rgba(0,0,0,0.3)',
    borderTopRightRadius: 24,
    borderBottomRightRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 2,
  },
  edgeArrow: {
    width: 0,
    height: 0,
    borderTopWidth: 8,
    borderBottomWidth: 8,
    borderRightWidth: 10,
    borderTopColor: 'transparent',
    borderBottomColor: 'transparent',
    borderRightColor: '#fff',
    marginLeft: 4,
  },
  swipeIndicator: {
    position: 'absolute',
    top: '50%',
    width: 30,
    height: 60,
    marginTop: -30,
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 10,
  },
  swipeIndicatorLeft: {
    left: 0,
    borderTopRightRadius: 15,
    borderBottomRightRadius: 15,
    backgroundColor: 'rgba(0, 0, 0, 0.15)',
  },
  swipeIndicatorRight: {
    right: 0,
    borderTopLeftRadius: 15,
    borderBottomLeftRadius: 15,
    backgroundColor: 'rgba(0, 0, 0, 0.15)',
  },
  swipeIndicatorArrow: {
    width: 10,
    height: 10,
    borderTopWidth: 2,
    borderRightWidth: 2,
    borderColor: '#fff',
  },
  swipeIndicatorArrowLeft: {
    transform: [{ rotate: '-135deg' }],
    marginLeft: 4,
  },
  swipeIndicatorArrowRight: {
    transform: [{ rotate: '45deg' }],
    marginRight: 4,
  },
});

export default {
  SwipeBackProvider,
  SwipeBackView,
  useSwipeBack,
  useEdgeSwipe,
};
