/**
 * Native Transitions
 *
 * Provides native-feeling transitions for navigation
 * and component animations.
 */

import React, { useEffect } from 'react';
import { StyleSheet, ViewStyle, Dimensions } from 'react-native';
import Animated, {
  useAnimatedStyle,
  useSharedValue,
  withSpring,
  withTiming,
  withDelay,
  withSequence,
  Easing,
  FadeIn,
  FadeOut,
  SlideInRight,
  SlideOutRight,
  SlideInUp,
  SlideOutDown,
  ZoomIn,
  ZoomOut,
  Layout,
} from 'react-native-reanimated';

const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get('window');

/**
 * Spring configurations for different use cases
 */
export const SpringConfig = {
  // Quick, snappy spring for buttons
  snappy: {
    damping: 15,
    stiffness: 400,
    mass: 0.5,
  },
  // Smooth spring for modals
  smooth: {
    damping: 20,
    stiffness: 200,
    mass: 0.8,
  },
  // Bouncy spring for playful animations
  bouncy: {
    damping: 10,
    stiffness: 150,
    mass: 1,
  },
  // Heavy spring for drag operations
  heavy: {
    damping: 30,
    stiffness: 300,
    mass: 1.2,
  },
};

/**
 * Timing configurations
 */
export const TimingConfig = {
  fast: {
    duration: 150,
    easing: Easing.out(Easing.cubic),
  },
  normal: {
    duration: 250,
    easing: Easing.out(Easing.cubic),
  },
  slow: {
    duration: 400,
    easing: Easing.out(Easing.cubic),
  },
};

/**
 * Animated component wrapper with fade in/out
 */
interface FadeViewProps {
  children: React.ReactNode;
  visible: boolean;
  duration?: number;
  delay?: number;
  style?: ViewStyle;
}

export function FadeView({
  children,
  visible,
  duration = 250,
  delay = 0,
  style,
}: FadeViewProps) {
  const opacity = useSharedValue(visible ? 1 : 0);

  useEffect(() => {
    opacity.value = withDelay(
      delay,
      withTiming(visible ? 1 : 0, { duration })
    );
  }, [visible, delay, duration, opacity]);

  const animatedStyle = useAnimatedStyle(() => ({
    opacity: opacity.value,
  }));

  if (!visible && opacity.value === 0) {
    return null;
  }

  return (
    <Animated.View style={[style, animatedStyle]}>{children}</Animated.View>
  );
}

/**
 * Animated component wrapper with slide transition
 */
interface SlideViewProps {
  children: React.ReactNode;
  visible: boolean;
  direction?: 'left' | 'right' | 'up' | 'down';
  distance?: number;
  duration?: number;
  style?: ViewStyle;
}

export function SlideView({
  children,
  visible,
  direction = 'right',
  distance = SCREEN_WIDTH,
  duration = 300,
  style,
}: SlideViewProps) {
  const translateX = useSharedValue(0);
  const translateY = useSharedValue(0);
  const opacity = useSharedValue(visible ? 1 : 0);

  useEffect(() => {
    const config = { duration };

    if (visible) {
      translateX.value = withTiming(0, config);
      translateY.value = withTiming(0, config);
      opacity.value = withTiming(1, config);
    } else {
      opacity.value = withTiming(0, config);
      switch (direction) {
        case 'left':
          translateX.value = withTiming(-distance, config);
          break;
        case 'right':
          translateX.value = withTiming(distance, config);
          break;
        case 'up':
          translateY.value = withTiming(-distance, config);
          break;
        case 'down':
          translateY.value = withTiming(distance, config);
          break;
      }
    }
  }, [visible, direction, distance, duration, translateX, translateY, opacity]);

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [
      { translateX: translateX.value },
      { translateY: translateY.value },
    ],
    opacity: opacity.value,
  }));

  return (
    <Animated.View style={[style, animatedStyle]}>{children}</Animated.View>
  );
}

/**
 * Animated component wrapper with scale transition
 */
interface ScaleViewProps {
  children: React.ReactNode;
  visible: boolean;
  initialScale?: number;
  style?: ViewStyle;
}

export function ScaleView({
  children,
  visible,
  initialScale = 0.8,
  style,
}: ScaleViewProps) {
  const scale = useSharedValue(visible ? 1 : initialScale);
  const opacity = useSharedValue(visible ? 1 : 0);

  useEffect(() => {
    if (visible) {
      scale.value = withSpring(1, SpringConfig.snappy);
      opacity.value = withTiming(1, TimingConfig.fast);
    } else {
      scale.value = withSpring(initialScale, SpringConfig.snappy);
      opacity.value = withTiming(0, TimingConfig.fast);
    }
  }, [visible, initialScale, scale, opacity]);

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }],
    opacity: opacity.value,
  }));

  return (
    <Animated.View style={[style, animatedStyle]}>{children}</Animated.View>
  );
}

/**
 * Pressable with scale feedback
 */
interface ScalePressableProps {
  children: React.ReactNode;
  onPress?: () => void;
  onLongPress?: () => void;
  scaleDown?: number;
  style?: ViewStyle;
  disabled?: boolean;
}

export function ScalePressable({
  children,
  onPress,
  onLongPress,
  scaleDown = 0.97,
  style,
  disabled = false,
}: ScalePressableProps) {
  const scale = useSharedValue(1);
  const pressed = useSharedValue(false);

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }],
  }));

  const handlePressIn = () => {
    scale.value = withSpring(scaleDown, SpringConfig.snappy);
    pressed.value = true;
  };

  const handlePressOut = () => {
    scale.value = withSpring(1, SpringConfig.snappy);
    pressed.value = false;
  };

  return (
    <Animated.View
      style={[style, animatedStyle]}
      onTouchStart={!disabled ? handlePressIn : undefined}
      onTouchEnd={!disabled ? handlePressOut : undefined}
      onTouchCancel={!disabled ? handlePressOut : undefined}
    >
      {children}
    </Animated.View>
  );
}

/**
 * Staggered list animation
 */
interface StaggeredListProps {
  children: React.ReactNode[];
  staggerDelay?: number;
  initialDelay?: number;
  animation?: 'fade' | 'slide' | 'scale';
}

export function StaggeredList({
  children,
  staggerDelay = 50,
  initialDelay = 0,
  animation = 'fade',
}: StaggeredListProps) {
  return (
    <>
      {React.Children.map(children, (child, index) => {
        const delay = initialDelay + index * staggerDelay;

        let enteringAnimation;
        switch (animation) {
          case 'slide':
            enteringAnimation = SlideInRight.delay(delay).springify();
            break;
          case 'scale':
            enteringAnimation = ZoomIn.delay(delay).springify();
            break;
          case 'fade':
          default:
            enteringAnimation = FadeIn.delay(delay).duration(300);
        }

        return (
          <Animated.View entering={enteringAnimation}>{child}</Animated.View>
        );
      })}
    </>
  );
}

/**
 * Parallax scroll animation
 */
interface ParallaxViewProps {
  children: React.ReactNode;
  scrollY: Animated.SharedValue<number>;
  parallaxFactor?: number;
  style?: ViewStyle;
}

export function ParallaxView({
  children,
  scrollY,
  parallaxFactor = 0.5,
  style,
}: ParallaxViewProps) {
  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ translateY: scrollY.value * parallaxFactor }],
  }));

  return (
    <Animated.View style={[style, animatedStyle]}>{children}</Animated.View>
  );
}

/**
 * Shared element transition helpers
 */
export function createSharedElementStyle(
  tag: string
): {
  sharedTransitionTag: string;
  sharedTransitionStyle: ViewStyle;
} {
  return {
    sharedTransitionTag: tag,
    sharedTransitionStyle: {
      // Styles that help with shared element transitions
    },
  };
}

/**
 * Prebuilt entering/exiting animations
 */
export const Animations = {
  // Entering animations
  entering: {
    fadeIn: FadeIn,
    fadeInFast: FadeIn.duration(150),
    fadeInSlow: FadeIn.duration(400),
    slideInRight: SlideInRight,
    slideInUp: SlideInUp,
    zoomIn: ZoomIn,
    bounce: FadeIn.springify().damping(8).stiffness(100),
  },

  // Exiting animations
  exiting: {
    fadeOut: FadeOut,
    fadeOutFast: FadeOut.duration(150),
    fadeOutSlow: FadeOut.duration(400),
    slideOutRight: SlideOutRight,
    slideOutDown: SlideOutDown,
    zoomOut: ZoomOut,
  },

  // Layout animations
  layout: {
    default: Layout,
    spring: Layout.springify(),
    linear: Layout.duration(200),
  },
};

export default {
  SpringConfig,
  TimingConfig,
  FadeView,
  SlideView,
  ScaleView,
  ScalePressable,
  StaggeredList,
  ParallaxView,
  Animations,
};
