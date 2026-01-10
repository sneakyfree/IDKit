/**
 * Pull to Refresh Component
 *
 * A customizable pull-to-refresh wrapper with native feel.
 */

import React, { useCallback, useState } from 'react';
import {
  RefreshControl,
  ScrollView,
  ScrollViewProps,
  StyleSheet,
  View,
  Platform,
} from 'react-native';
import Animated, {
  useAnimatedStyle,
  useSharedValue,
  withSpring,
  interpolate,
  Extrapolation,
} from 'react-native-reanimated';
import { HapticPresets } from './HapticFeedback';

interface PullToRefreshProps extends ScrollViewProps {
  onRefresh: () => Promise<void>;
  refreshing?: boolean;
  children: React.ReactNode;
  refreshColor?: string;
  refreshBackgroundColor?: string;
  progressViewOffset?: number;
  disabled?: boolean;
  CustomRefreshIndicator?: React.ComponentType<{
    refreshing: boolean;
    pullProgress: Animated.SharedValue<number>;
  }>;
}

/**
 * Default refresh indicator with animated spinner
 */
function DefaultRefreshIndicator({
  refreshing,
  pullProgress,
}: {
  refreshing: boolean;
  pullProgress: Animated.SharedValue<number>;
}) {
  const animatedStyle = useAnimatedStyle(() => {
    const rotate = interpolate(
      pullProgress.value,
      [0, 1],
      [0, 360],
      Extrapolation.CLAMP
    );

    const scale = interpolate(
      pullProgress.value,
      [0, 0.5, 1],
      [0.5, 0.8, 1],
      Extrapolation.CLAMP
    );

    return {
      transform: [
        { rotate: `${rotate}deg` },
        { scale: refreshing ? 1 : scale },
      ],
      opacity: pullProgress.value > 0.1 ? 1 : 0,
    };
  });

  return (
    <Animated.View style={[styles.indicator, animatedStyle]}>
      <View style={styles.spinnerDot} />
    </Animated.View>
  );
}

export function PullToRefresh({
  onRefresh,
  refreshing: externalRefreshing,
  children,
  refreshColor = '#3b82f6',
  refreshBackgroundColor,
  progressViewOffset = 0,
  disabled = false,
  CustomRefreshIndicator,
  ...scrollViewProps
}: PullToRefreshProps) {
  const [internalRefreshing, setInternalRefreshing] = useState(false);
  const pullProgress = useSharedValue(0);

  const refreshing = externalRefreshing ?? internalRefreshing;

  const handleRefresh = useCallback(async () => {
    if (disabled || refreshing) return;

    setInternalRefreshing(true);
    HapticPresets.refreshStart();

    try {
      await onRefresh();
      HapticPresets.refreshComplete();
    } catch (error) {
      HapticPresets.error();
    } finally {
      setInternalRefreshing(false);
      pullProgress.value = withSpring(0);
    }
  }, [onRefresh, disabled, refreshing, pullProgress]);

  const RefreshIndicator = CustomRefreshIndicator || DefaultRefreshIndicator;

  return (
    <ScrollView
      {...scrollViewProps}
      refreshControl={
        <RefreshControl
          refreshing={refreshing}
          onRefresh={handleRefresh}
          tintColor={refreshColor}
          colors={[refreshColor]}
          progressBackgroundColor={refreshBackgroundColor}
          progressViewOffset={progressViewOffset}
          enabled={!disabled}
        />
      }
    >
      {children}
    </ScrollView>
  );
}

/**
 * Custom pull-to-refresh with more control over the animation
 */
interface CustomPullToRefreshProps {
  onRefresh: () => Promise<void>;
  refreshing?: boolean;
  children: React.ReactNode;
  threshold?: number;
  maxPullDistance?: number;
}

export function CustomPullToRefresh({
  onRefresh,
  refreshing = false,
  children,
  threshold = 80,
  maxPullDistance = 150,
}: CustomPullToRefreshProps) {
  const pullDistance = useSharedValue(0);
  const isRefreshing = useSharedValue(false);

  const containerStyle = useAnimatedStyle(() => {
    return {
      transform: [
        {
          translateY: interpolate(
            pullDistance.value,
            [0, maxPullDistance],
            [0, maxPullDistance / 2],
            Extrapolation.CLAMP
          ),
        },
      ],
    };
  });

  const indicatorStyle = useAnimatedStyle(() => {
    const progress = pullDistance.value / threshold;
    const opacity = interpolate(progress, [0, 0.5, 1], [0, 0.5, 1]);
    const scale = interpolate(progress, [0, 1], [0.5, 1], Extrapolation.CLAMP);
    const rotate = interpolate(progress, [0, 1], [0, 180]);

    return {
      opacity,
      transform: [{ scale }, { rotate: `${rotate}deg` }],
    };
  });

  return (
    <View style={styles.customContainer}>
      <Animated.View style={[styles.customIndicatorContainer, indicatorStyle]}>
        <View style={styles.customIndicator} />
      </Animated.View>
      <Animated.View style={[styles.customContent, containerStyle]}>
        {children}
      </Animated.View>
    </View>
  );
}

/**
 * FlatList with pull-to-refresh support
 */
import { FlatList, FlatListProps } from 'react-native';

export function RefreshableFlatList<T>({
  onRefresh,
  refreshing,
  refreshColor = '#3b82f6',
  ...props
}: FlatListProps<T> & {
  onRefresh: () => Promise<void>;
  refreshing?: boolean;
  refreshColor?: string;
}) {
  const [internalRefreshing, setInternalRefreshing] = useState(false);
  const isRefreshing = refreshing ?? internalRefreshing;

  const handleRefresh = useCallback(async () => {
    setInternalRefreshing(true);
    HapticPresets.refreshStart();

    try {
      await onRefresh();
      HapticPresets.refreshComplete();
    } catch (error) {
      HapticPresets.error();
    } finally {
      setInternalRefreshing(false);
    }
  }, [onRefresh]);

  return (
    <FlatList
      {...props}
      refreshControl={
        <RefreshControl
          refreshing={isRefreshing}
          onRefresh={handleRefresh}
          tintColor={refreshColor}
          colors={[refreshColor]}
        />
      }
    />
  );
}

const styles = StyleSheet.create({
  indicator: {
    width: 24,
    height: 24,
    justifyContent: 'center',
    alignItems: 'center',
  },
  spinnerDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#3b82f6',
  },
  customContainer: {
    flex: 1,
    position: 'relative',
  },
  customIndicatorContainer: {
    position: 'absolute',
    top: 20,
    left: 0,
    right: 0,
    alignItems: 'center',
    zIndex: 1,
  },
  customIndicator: {
    width: 32,
    height: 32,
    borderRadius: 16,
    borderWidth: 2,
    borderColor: '#3b82f6',
    borderTopColor: 'transparent',
  },
  customContent: {
    flex: 1,
  },
});

export default PullToRefresh;
