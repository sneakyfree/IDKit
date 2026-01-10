/**
 * Message Item Component
 */

import { View, Text, Image, Pressable, StyleSheet } from 'react-native';

import { useTheme } from '@/lib/theme';

interface MessageItemProps {
  conversation: any;
  onPress: () => void;
}

export function MessageItem({ conversation, onPress }: MessageItemProps) {
  const { colors } = useTheme();

  return (
    <Pressable
      style={[styles.container, { backgroundColor: colors.background }]}
      onPress={onPress}
    >
      <View style={styles.avatarContainer}>
        <Image
          source={{ uri: conversation.participant?.avatar_url || 'https://via.placeholder.com/52' }}
          style={styles.avatar}
        />
        {conversation.unread_count > 0 && (
          <View style={[styles.unreadBadge, { backgroundColor: colors.primary }]}>
            <Text style={styles.unreadText}>
              {conversation.unread_count > 99 ? '99+' : conversation.unread_count}
            </Text>
          </View>
        )}
      </View>

      <View style={styles.content}>
        <View style={styles.header}>
          <Text style={[styles.name, { color: colors.text }]} numberOfLines={1}>
            {conversation.participant?.display_name || 'User'}
          </Text>
          <Text style={[styles.time, { color: colors.textSecondary }]}>
            {formatTime(conversation.last_message_at)}
          </Text>
        </View>

        <Text
          style={[
            styles.lastMessage,
            {
              color: conversation.unread_count > 0 ? colors.text : colors.textSecondary,
              fontWeight: conversation.unread_count > 0 ? '500' : 'normal',
            },
          ]}
          numberOfLines={1}
        >
          {conversation.last_message || 'No messages yet'}
        </Text>

        {conversation.platform && (
          <Text style={[styles.platform, { color: colors.textSecondary }]}>
            via {conversation.platform}
          </Text>
        )}
      </View>
    </Pressable>
  );
}

function formatTime(dateString: string): string {
  if (!dateString) return '';

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
    paddingHorizontal: 16,
    gap: 12,
  },
  avatarContainer: {
    position: 'relative',
  },
  avatar: {
    width: 52,
    height: 52,
    borderRadius: 26,
  },
  unreadBadge: {
    position: 'absolute',
    top: -2,
    right: -2,
    minWidth: 20,
    height: 20,
    borderRadius: 10,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 4,
  },
  unreadText: {
    color: '#FFF',
    fontSize: 11,
    fontWeight: 'bold',
  },
  content: {
    flex: 1,
    gap: 2,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  name: {
    fontSize: 15,
    fontWeight: '600',
    flex: 1,
  },
  time: {
    fontSize: 12,
  },
  lastMessage: {
    fontSize: 14,
  },
  platform: {
    fontSize: 11,
    marginTop: 2,
  },
});
