/**
 * Post Grid Item Component
 */

import { View, Image, Pressable, StyleSheet, Text } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

interface PostGridItemProps {
  post: any;
  size: number;
  onPress: () => void;
}

export function PostGridItem({ post, size, onPress }: PostGridItemProps) {
  const isVideo = post.post_type === 'video' || post.post_type === 'podcast_clip';
  const isCarousel = post.post_type === 'carousel';

  return (
    <Pressable
      style={[styles.container, { width: size, height: size }]}
      onPress={onPress}
    >
      <Image
        source={{ uri: post.thumbnail_url || post.media_urls?.[0] || 'https://via.placeholder.com/150' }}
        style={styles.image}
        resizeMode="cover"
      />

      {/* Type indicator */}
      <View style={styles.typeIndicator}>
        {isVideo && <Ionicons name="play" size={14} color="#FFF" />}
        {isCarousel && <Ionicons name="copy" size={14} color="#FFF" />}
      </View>

      {/* View count for videos */}
      {isVideo && post.view_count > 0 && (
        <View style={styles.viewCount}>
          <Ionicons name="play" size={10} color="#FFF" />
          <Text style={styles.viewCountText}>{formatCount(post.view_count)}</Text>
        </View>
      )}
    </Pressable>
  );
}

function formatCount(count: number): string {
  if (count >= 1000000) return (count / 1000000).toFixed(1) + 'M';
  if (count >= 1000) return (count / 1000).toFixed(1) + 'K';
  return count.toString();
}

const styles = StyleSheet.create({
  container: {
    position: 'relative',
    marginBottom: 2,
  },
  image: {
    flex: 1,
    backgroundColor: '#1A1A1A',
  },
  typeIndicator: {
    position: 'absolute',
    top: 6,
    right: 6,
  },
  viewCount: {
    position: 'absolute',
    bottom: 6,
    left: 6,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  viewCountText: {
    color: '#FFF',
    fontSize: 12,
    fontWeight: '600',
  },
});
