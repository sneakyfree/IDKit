/**
 * UX Components Index
 *
 * Mobile-specific UX improvements including haptic feedback,
 * pull-to-refresh, swipe gestures, bottom sheets, and native transitions.
 */

// Haptic Feedback
export {
  triggerHaptic,
  useHaptic,
  withHaptic,
  HapticPresets,
  type HapticType,
} from './HapticFeedback';
export { default as HapticFeedback } from './HapticFeedback';

// Pull to Refresh
export {
  PullToRefresh,
  CustomPullToRefresh,
  RefreshableFlatList,
} from './PullToRefresh';
export { default as PullToRefreshDefault } from './PullToRefresh';

// Swipeable Row
export {
  SwipeableRow,
  SwipeToDeleteRow,
  SwipeToArchiveRow,
  type SwipeAction,
} from './SwipeableRow';
export { default as SwipeableRowDefault } from './SwipeableRow';

// Bottom Sheet
export {
  BottomSheet,
  ActionSheet,
  type BottomSheetRef,
} from './BottomSheet';
export { default as BottomSheetDefault } from './BottomSheet';

// Native Transitions
export {
  SpringConfig,
  TimingConfig,
  FadeView,
  SlideView,
  ScaleView,
  ScalePressable,
  StaggeredList,
  ParallaxView,
  Animations,
} from './NativeTransitions';
export { default as NativeTransitions } from './NativeTransitions';

// Gesture Navigation
export { useSwipeBack, SwipeBackProvider } from './GestureNavigation';
