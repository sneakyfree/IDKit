/**
 * Notification Item Component
 */

import { View, Text, Image, Pressable, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

import { useTheme } from '@/lib/theme';

interface NotificationItemProps {
  notification: any;
  onPress: () => void;
}

export function NotificationItem({ notification, onPress }: NotificationItemProps) {
  const { colors } = useTheme();

  const getIcon = () => {
    switch (notification.type) {
      case 'like':
        return <Ionicons name="heart" size={20} color="#FF6B6B" />;
      case 'comment':
        return <Ionicons name="chatbubble" size={20} color={colors.primary} />;
      case 'follow':
        return <Ionicons name="person-add" size={20} color="#00B894" />;
      case 'mention':
        return <Ionicons name="at" size={20} color="#FDCB6E" />;
      default:
        return <Ionicons name="notifications" size={20} color={colors.textSecondary} />;
    }
  };

  return (
    <Pressable
      style={[
        styles.container,
        { backgroundColor: notification.is_read ? colors.background : colors.surface },
      ]}
      onPress={onPress}
    >
      <View style={styles.iconContainer}>{getIcon()}</View>

      <Image
        source={{ uri: notification.actor?.avatar_url || 'https://via.placeholder.com/40' }}
        style={styles.avatar}
      />

      <View style={styles.content}>
        <Text style={[styles.text, { color: colors.text }]} numberOfLines={2}>
          <Text style={styles.username}>{notification.actor?.username || 'Someone'}</Text>
          {' '}
          {notification.message}
        </Text>
        <Text style={[styles.time, { color: colors.textSecondary }]}>
          {formatTime(notification.created_at)}
        </Text>
      </View>

      {notification.post?.thumbnail_url && (
        <Image
          source={{ uri: notification.post.thumbnail_url }}
          style={styles.thumbnail}
        />
      )}
    </Pressable>
  );
}

function formatTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 1) return 'now';
  if (diffMins < 60) return `${diffMins}m`;
  if (diffHours < 24) return `${diffHours}h`;
  if (diffDays < 7) return `${diffDays}d`;
  return date.toLocaleDateString();
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    gap: 10,
  },
  iconContainer: {
    width: 24,
    alignItems: 'center',
  },
  avatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
  },
  content: {
    flex: 1,
    gap: 2,
  },
  text: {
    fontSize: 14,
    lineHeight: 20,
  },
  username: {
    fontWeight: '600',
  },
  time: {
    fontSize: 12,
  },
  thumbnail: {
    width: 44,
    height: 44,
    borderRadius: 6,
  },
});
