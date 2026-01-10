/**
 * Feed Post Component
 *
 * Full-screen post card for the TikTok-style feed.
 */

import { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  Image,
  Pressable,
  StyleSheet,
  Dimensions,
} from 'react-native';
import { Video, ResizeMode, AVPlaybackStatus } from 'expo-av';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import * as Haptics from 'expo-haptics';

import { useTheme } from '@/lib/theme';
import { useFeed } from '@/hooks/useFeed';
import type { Post } from '@/types/feed';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

interface FeedPostProps {
  post: Post;
  isActive: boolean;
  height: number;
}

export function FeedPost({ post, isActive, height }: FeedPostProps) {
  const { colors } = useTheme();
  const router = useRouter();
  const videoRef = useRef<Video>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);

  const { likePost, unlikePost, savePost } = useFeed();

  // Control video playback based on visibility
  useEffect(() => {
    if (videoRef.current) {
      if (isActive) {
        videoRef.current.playAsync();
        setIsPlaying(true);
      } else {
        videoRef.current.pauseAsync();
        setIsPlaying(false);
      }
    }
  }, [isActive]);

  const handleDoubleTap = () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    if (!post.is_liked) {
      likePost(post.id);
    }
  };

  const handleLike = () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    if (post.is_liked) {
      unlikePost(post.id);
    } else {
      likePost(post.id);
    }
  };

  const handleSave = () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    savePost(post.id);
  };

  const handleComment = () => {
    router.push(`/post/${post.id}/comments`);
  };

  const handleShare = () => {
    // Open share sheet
  };

  const handleProfilePress = () => {
    router.push(`/profile/${post.author.username}`);
  };

  const toggleMute = () => {
    setIsMuted(!isMuted);
  };

  const isVideo = post.post_type === 'video' || post.post_type === 'podcast_clip';
  const mediaUrl = post.media_urls[0] || '';

  return (
    <View style={[styles.container, { height }]}>
      {/* Media Content */}
      <Pressable style={styles.mediaContainer} onPress={toggleMute}>
        {isVideo ? (
          <Video
            ref={videoRef}
            source={{ uri: mediaUrl }}
            style={styles.video}
            resizeMode={ResizeMode.COVER}
            isLooping
            isMuted={isMuted}
            shouldPlay={isActive}
          />
        ) : (
          <Image
            source={{ uri: mediaUrl || post.thumbnail_url }}
            style={styles.image}
            resizeMode="cover"
          />
        )}
      </Pressable>

      {/* Overlay Content */}
      <View style={styles.overlay}>
        {/* Right Side Actions */}
        <View style={styles.actionsContainer}>
          {/* Profile */}
          <Pressable style={styles.actionItem} onPress={handleProfilePress}>
            <Image
              source={{ uri: post.author.avatar_url || 'https://via.placeholder.com/48' }}
              style={styles.avatar}
            />
            {!post.is_following_author && (
              <View style={[styles.followBadge, { backgroundColor: colors.primary }]}>
                <Ionicons name="add" size={12} color="#FFF" />
              </View>
            )}
          </Pressable>

          {/* Like */}
          <Pressable style={styles.actionItem} onPress={handleLike}>
            <Ionicons
              name={post.is_liked ? 'heart' : 'heart-outline'}
              size={32}
              color={post.is_liked ? '#FF6B6B' : '#FFF'}
            />
            <Text style={styles.actionText}>
              {formatCount(post.like_count)}
            </Text>
          </Pressable>

          {/* Comment */}
          <Pressable style={styles.actionItem} onPress={handleComment}>
            <Ionicons name="chatbubble-ellipses-outline" size={30} color="#FFF" />
            <Text style={styles.actionText}>
              {formatCount(post.comment_count)}
            </Text>
          </Pressable>

          {/* Save */}
          <Pressable style={styles.actionItem} onPress={handleSave}>
            <Ionicons
              name={post.is_saved ? 'bookmark' : 'bookmark-outline'}
              size={30}
              color={post.is_saved ? colors.primary : '#FFF'}
            />
            <Text style={styles.actionText}>
              {formatCount(post.save_count)}
            </Text>
          </Pressable>

          {/* Share */}
          <Pressable style={styles.actionItem} onPress={handleShare}>
            <Ionicons name="arrow-redo-outline" size={30} color="#FFF" />
            <Text style={styles.actionText}>Share</Text>
          </Pressable>
        </View>

        {/* Bottom Content */}
        <View style={styles.bottomContent}>
          {/* Author */}
          <Pressable onPress={handleProfilePress}>
            <Text style={styles.username}>@{post.author.username}</Text>
          </Pressable>

          {/* Caption */}
          {post.content_text && (
            <Text style={styles.caption} numberOfLines={3}>
              {post.content_text}
            </Text>
          )}

          {/* Hashtags */}
          {post.hashtags.length > 0 && (
            <Text style={styles.hashtags} numberOfLines={1}>
              {post.hashtags.map(h => `#${h}`).join(' ')}
            </Text>
          )}

          {/* Audio Info */}
          {post.audio_info && (
            <View style={styles.audioInfo}>
              <Ionicons name="musical-notes" size={14} color="#FFF" />
              <Text style={styles.audioText} numberOfLines={1}>
                {post.audio_info.name} - {post.audio_info.artist}
              </Text>
            </View>
          )}
        </View>
      </View>

      {/* Mute Indicator */}
      {isVideo && isMuted && (
        <View style={styles.muteIndicator}>
          <Ionicons name="volume-mute" size={20} color="#FFF" />
        </View>
      )}
    </View>
  );
}

function formatCount(count: number): string {
  if (count >= 1000000) {
    return (count / 1000000).toFixed(1) + 'M';
  }
  if (count >= 1000) {
    return (count / 1000).toFixed(1) + 'K';
  }
  return count.toString();
}

const styles = StyleSheet.create({
  container: {
    width: SCREEN_WIDTH,
    backgroundColor: '#000',
  },
  mediaContainer: {
    flex: 1,
  },
  video: {
    flex: 1,
  },
  image: {
    flex: 1,
  },
  overlay: {
    ...StyleSheet.absoluteFillObject,
    flexDirection: 'row',
    justifyContent: 'flex-end',
  },
  actionsContainer: {
    position: 'absolute',
    right: 8,
    bottom: 100,
    alignItems: 'center',
    gap: 16,
  },
  actionItem: {
    alignItems: 'center',
    gap: 4,
  },
  avatar: {
    width: 48,
    height: 48,
    borderRadius: 24,
    borderWidth: 2,
    borderColor: '#FFF',
  },
  followBadge: {
    position: 'absolute',
    bottom: -6,
    width: 18,
    height: 18,
    borderRadius: 9,
    justifyContent: 'center',
    alignItems: 'center',
  },
  actionText: {
    color: '#FFF',
    fontSize: 12,
    fontWeight: '600',
  },
  bottomContent: {
    position: 'absolute',
    left: 12,
    right: 70,
    bottom: 20,
    gap: 8,
  },
  username: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: 'bold',
  },
  caption: {
    color: '#FFF',
    fontSize: 14,
    lineHeight: 20,
  },
  hashtags: {
    color: '#CCC',
    fontSize: 13,
  },
  audioInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  audioText: {
    color: '#FFF',
    fontSize: 13,
  },
  muteIndicator: {
    position: 'absolute',
    top: 60,
    right: 16,
    backgroundColor: 'rgba(0,0,0,0.5)',
    padding: 8,
    borderRadius: 20,
  },
});
