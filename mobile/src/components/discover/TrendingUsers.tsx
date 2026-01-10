/**
 * Trending Users Component
 */

import { View, Text, FlatList, Image, Pressable, StyleSheet } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

import { useTheme } from '@/lib/theme';

interface TrendingUsersProps {
  users: any[];
}

export function TrendingUsers({ users }: TrendingUsersProps) {
  const { colors } = useTheme();
  const router = useRouter();

  const renderItem = ({ item }: { item: any }) => (
    <Pressable
      style={[styles.item, { backgroundColor: colors.surface }]}
      onPress={() => router.push(`/profile/${item.username}`)}
    >
      <Image
        source={{ uri: item.avatar_url || 'https://via.placeholder.com/56' }}
        style={styles.avatar}
      />

      <View style={styles.content}>
        <View style={styles.nameRow}>
          <Text style={[styles.displayName, { color: colors.text }]}>
            {item.display_name}
          </Text>
          {item.is_verified && (
            <Ionicons name="checkmark-circle" size={16} color={colors.primary} />
          )}
        </View>
        <Text style={[styles.username, { color: colors.textSecondary }]}>
          @{item.username}
        </Text>
        <Text style={[styles.followers, { color: colors.textSecondary }]}>
          {formatFollowers(item.follower_count)} followers
        </Text>
      </View>

      <Pressable
        style={[
          styles.followButton,
          item.is_following
            ? { backgroundColor: colors.surface, borderColor: colors.border, borderWidth: 1 }
            : { backgroundColor: colors.primary },
        ]}
      >
        <Text
          style={[
            styles.followButtonText,
            { color: item.is_following ? colors.text : '#FFF' },
          ]}
        >
          {item.is_following ? 'Following' : 'Follow'}
        </Text>
      </Pressable>
    </Pressable>
  );

  return (
    <FlatList
      data={users}
      renderItem={renderItem}
      keyExtractor={(item) => item.id}
      contentContainerStyle={styles.list}
      showsVerticalScrollIndicator={false}
      ListEmptyComponent={
        <View style={styles.empty}>
          <Ionicons name="people-outline" size={48} color={colors.textSecondary} />
          <Text style={[styles.emptyText, { color: colors.textSecondary }]}>
            No trending users
          </Text>
        </View>
      }
    />
  );
}

function formatFollowers(count: number): string {
  if (count >= 1000000) return (count / 1000000).toFixed(1) + 'M';
  if (count >= 1000) return (count / 1000).toFixed(1) + 'K';
  return count.toString();
}

const styles = StyleSheet.create({
  list: {
    padding: 16,
    gap: 8,
  },
  item: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    borderRadius: 12,
    gap: 12,
  },
  avatar: {
    width: 56,
    height: 56,
    borderRadius: 28,
  },
  content: {
    flex: 1,
    gap: 2,
  },
  nameRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  displayName: {
    fontSize: 15,
    fontWeight: '600',
  },
  username: {
    fontSize: 13,
  },
  followers: {
    fontSize: 12,
  },
  followButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
  },
  followButtonText: {
    fontSize: 13,
    fontWeight: '600',
  },
  empty: {
    alignItems: 'center',
    paddingVertical: 60,
    gap: 12,
  },
  emptyText: {
    fontSize: 16,
  },
});
