/**
 * Home Feed Screen
 *
 * TikTok-style vertical scroll feed - the PRIMARY screen.
 * This is what users see first after logging in.
 */

import { useCallback, useState, useRef } from 'react';
import {
  View,
  FlatList,
  Dimensions,
  StyleSheet,
  RefreshControl,
  ViewToken,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { FeedPost } from '@/components/feed/FeedPost';
import { FeedHeader } from '@/components/feed/FeedHeader';
import { useFeed } from '@/hooks/useFeed';
import { useTheme } from '@/lib/theme';
import type { Post } from '@/types/feed';

const { height: SCREEN_HEIGHT } = Dimensions.get('window');
const TAB_BAR_HEIGHT = 85;
const POST_HEIGHT = SCREEN_HEIGHT - TAB_BAR_HEIGHT;

export default function HomeFeedScreen() {
  const insets = useSafeAreaInsets();
  const { colors } = useTheme();
  const [activeIndex, setActiveIndex] = useState(0);

  const {
    data,
    isLoading,
    isRefreshing,
    fetchNextPage,
    hasNextPage,
    refetch,
  } = useFeed();

  const posts = data?.pages.flatMap((page) => page.posts) ?? [];

  const onViewableItemsChanged = useCallback(
    ({ viewableItems }: { viewableItems: ViewToken[] }) => {
      if (viewableItems.length > 0 && viewableItems[0].index !== null) {
        setActiveIndex(viewableItems[0].index);
      }
    },
    []
  );

  const viewabilityConfig = useRef({
    itemVisiblePercentThreshold: 80,
  }).current;

  const renderPost = useCallback(
    ({ item, index }: { item: Post; index: number }) => (
      <FeedPost
        post={item}
        isActive={index === activeIndex}
        height={POST_HEIGHT - insets.top}
      />
    ),
    [activeIndex, insets.top]
  );

  const handleEndReached = useCallback(() => {
    if (hasNextPage) {
      fetchNextPage();
    }
  }, [hasNextPage, fetchNextPage]);

  const keyExtractor = useCallback((item: Post) => item.id, []);

  const getItemLayout = useCallback(
    (_: any, index: number) => ({
      length: POST_HEIGHT - insets.top,
      offset: (POST_HEIGHT - insets.top) * index,
      index,
    }),
    [insets.top]
  );

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <FeedHeader />

      <FlatList
        data={posts}
        renderItem={renderPost}
        keyExtractor={keyExtractor}
        pagingEnabled
        showsVerticalScrollIndicator={false}
        snapToInterval={POST_HEIGHT - insets.top}
        snapToAlignment="start"
        decelerationRate="fast"
        onViewableItemsChanged={onViewableItemsChanged}
        viewabilityConfig={viewabilityConfig}
        onEndReached={handleEndReached}
        onEndReachedThreshold={0.5}
        getItemLayout={getItemLayout}
        refreshControl={
          <RefreshControl
            refreshing={isRefreshing}
            onRefresh={refetch}
            tintColor={colors.primary}
          />
        }
        contentContainerStyle={{
          paddingTop: insets.top,
        }}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
});
